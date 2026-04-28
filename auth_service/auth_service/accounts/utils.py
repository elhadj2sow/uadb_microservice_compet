import threading
import logging
try:
    import requests as _requests
except ImportError:
    _requests = None

logger = logging.getLogger(__name__)

# URL du service audit centralisé (configurée dans .env)
try:
    from django.conf import settings as _settings
    _AUDIT_URL   = getattr(_settings, 'AUDIT_SERVICE_URL',   'http://localhost:8008')
    _SERVICE_TOK = getattr(_settings, 'INTERNAL_SERVICE_TOKEN', '')
except Exception:
    _AUDIT_URL   = 'http://localhost:8008'
    _SERVICE_TOK = ''


def _envoyer_audit(payload):
    """Envoie une entrée au service audit en arrière-plan (non bloquant)."""
    if not _requests:
        return
    try:
        _requests.post(
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
    payload = {
        'action'        : action,
        'service'       : 'auth',
        'ressource'     : ressource,
        'acteur'        : user.username if user else 'anonyme',
        'utilisateur_id': user.pk if user else None,
        'role_acteur'   : (
            list(user.roles.values_list('libelle', flat=True))[0]
            if user and hasattr(user, 'roles') and user.roles.exists()
            else ''
        ),
        'adresse_ip'    : get_client_ip(request),
        'methode_http'  : request.method,
        'url'           : request.path,
        'details'       : details or {},
        'niveau'        : 'INFO',
        'statut'        : 'succes',
    }
    threading.Thread(target=_envoyer_audit, args=(payload,), daemon=True).start()


def get_client_ip(request):
    """Récupère l'IP réelle du client (derrière proxy)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
