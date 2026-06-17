import requests
import logging
import threading
import time
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Cache token interne (évite un appel HTTP à chaque requête) ────────────────
_token_cache = {'token': '', 'expires_at': 0}
_TOKEN_TTL   = 240  # secondes (4 min)


def get_internal_token():
    """Token JWT pour les appels inter-services, mis en cache 4 min."""
    now = time.time()
    if _token_cache['token'] and now < _token_cache['expires_at']:
        return _token_cache['token']
    try:
        res = requests.post(
            f"{settings.SERVICE_AUTH}/api/auth/login/",
            json={
                'username': settings.SERVICE_INTERNAL_USER,
                'password': settings.SERVICE_INTERNAL_PASSWORD,
            },
            timeout=5
        )
        token = res.json().get('access', '')
        if token:
            _token_cache['token']      = token
            _token_cache['expires_at'] = now + _TOKEN_TTL
        return token
    except Exception as e:
        logger.warning(f"Token interne non obtenu : {e}")
        return _token_cache['token']  # retourner le dernier token connu si dispo


def auth_header():
    token = get_internal_token()
    return {'Authorization': f'Bearer {token}'} if token else {}


def get_unites_formation(formation_id):
    """Retourne les UEs officielles d'une formation depuis dossier_service."""
    try:
        res = requests.get(
            f"{settings.SERVICE_DOSSIER}/api/formations/{formation_id}/ues/",
            headers=auth_header(),
            timeout=5
        )
        if res.status_code != 200:
            logger.warning(
                "Impossible de charger les UEs formation=%s (status=%s)",
                formation_id,
                res.status_code,
            )
            return []
        return res.json().get('ues', [])
    except Exception as e:
        logger.warning(
            "Erreur récupération UEs formation=%s : %s",
            formation_id,
            e,
        )
        return []


def get_etudiants_noms(ids):
    """Retourne {id: nom_complet} depuis auth_service pour une liste d'IDs."""
    if not ids:
        return {}
    try:
        ids_str = ','.join(str(i) for i in ids)
        res = requests.get(
            f"{settings.SERVICE_AUTH}/api/auth/etudiants/noms/?ids={ids_str}",
            headers=auth_header(),
            timeout=5
        )
        if res.ok:
            return {int(k): v for k, v in res.json().items()}
        logger.warning(f"get_etudiants_noms : status={res.status_code}")
        return {}
    except Exception as e:
        logger.warning(f"Impossible de récupérer les noms étudiants : {e}")
        return {}


def notifier_etudiant(etudiant_id, message, canal='email'):
    """Notifie un étudiant via le service notification."""
    try:
        requests.post(
            f"{settings.SERVICE_NOTIFICATION}/api/notifications/",
            json={
                'etudiant_id': etudiant_id,
                'canal'      : canal,
                'message'    : message,
            },
            headers = auth_header(),
            timeout = 5
        )
    except Exception as e:
        logger.warning(f"Notification étudiant {etudiant_id} échouée : {e}")


def appeler_moteur_regles(moyenne, credits, etudiant_id, deliberation_id):
    """
    Appelle le service IA pour calculer la décision
    et la mention selon les règles métier.
    Retourne dict avec 'decision' et 'mention'.
    """
    try:
        res = requests.post(
            f"{settings.SERVICE_IA}/api/evaluer/",
            json={
                'type'           : 'validation_deliberation',
                'moyenne'        : float(moyenne),
                'credits'        : int(credits),
                'etudiant'       : etudiant_id,
                'deliberation_id': deliberation_id,
            },
            headers = auth_header(),
            timeout = 5
        )
        if res.ok:
            return res.json()
        logger.warning(f"Service IA a répondu {res.status_code} — secours activé")
        return _regles_secours(float(moyenne), int(credits))
    except Exception as e:
        logger.warning(f"Service IA indisponible : {e}")
        # Règles de secours locales si service IA indisponible
        return _regles_secours(float(moyenne), int(credits))


def _regles_secours(moyenne, credits):
    """Règles métier de secours si le service IA est indisponible."""
    if moyenne >= 10 and credits >= 60:
        decision = 'admis'
    elif moyenne >= 8:
        decision = 'rattrapage'
    else:
        decision = 'ajourné'

    if moyenne >= 16:
        mention = 'tres_bien'
    elif moyenne >= 14:
        mention = 'bien'
    elif moyenne >= 12:
        mention = 'assez_bien'
    elif moyenne >= 10:
        mention = 'passable'
    else:
        mention = ''

    return {'decision': decision, 'mention': mention}


# ─────────────────────────────────────────────
#  AUDIT
# ─────────────────────────────────────────────

try:
    _AUDIT_URL   = getattr(settings, 'AUDIT_SERVICE_URL',   'http://localhost:8008')
    _SERVICE_TOK = getattr(settings, 'INTERNAL_SERVICE_TOKEN', '')
except Exception:
    _AUDIT_URL   = 'http://localhost:8008'
    _SERVICE_TOK = ''


def _envoyer_audit(payload):
    """Envoie une entrée au service audit en arrière-plan (non bloquant)."""
    try:
        requests.post(
            f'{_AUDIT_URL}/api/audit/tracer/',
            json=payload,
            headers={'X-Service-Token': _SERVICE_TOK},
            timeout=3,
        )
    except Exception as exc:
        logger.debug('Audit non disponible: %s', exc)


def tracer_action(request, action, ressource, details=None, utilisateur=None):
    """
    Enregistre une action dans le journal d'audit centralisé.
    L'envoi se fait en arrière-plan (thread) pour ne pas bloquer la réponse.
    """
    user = utilisateur or (
        request.user if hasattr(request, 'user') and request.user.is_authenticated else None
    )
    roles = getattr(user, 'roles', []) if user else []
    role_acteur = roles[0] if roles else ''

    payload = {
        'action'        : action,
        'service'       : 'deliberation',
        'ressource'     : ressource,
        'acteur'        : getattr(user, 'username', 'anonyme') if user else 'anonyme',
        'utilisateur_id': getattr(user, 'id', None) if user else None,
        'role_acteur'   : role_acteur,
        'adresse_ip'    : _get_client_ip(request),
        'methode_http'  : request.method,
        'url'           : request.path,
        'details'       : details or {},
        'niveau'        : 'INFO',
        'statut'        : 'succes',
    }
    threading.Thread(target=_envoyer_audit, args=(payload,), daemon=True).start()


def _get_client_ip(request):
    """Récupère l'IP réelle du client (derrière proxy)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
