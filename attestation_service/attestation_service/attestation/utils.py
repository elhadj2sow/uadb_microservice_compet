import time
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache du token interne : évite un login HTTP à chaque appel inter-service
_token_cache = {'token': '', 'expires_at': 0.0}


def get_internal_token():
    """Token JWT pour les appels inter-services (mis en cache 25 min)."""
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
            # JWT valide 30 min → on cache 25 min pour être sûr
            _token_cache['token']      = token
            _token_cache['expires_at'] = now + 25 * 60
        return token
    except Exception as e:
        logger.warning(f"Token interne non obtenu : {e}")
        # Retourner le token en cache même s'il est peut-être expiré
        return _token_cache.get('token', '')


def auth_header():
    token = get_internal_token()
    return {'Authorization': f'Bearer {token}'} if token else {}


def forwarded_auth_header(authorization_header=None):
    if authorization_header:
        return {'Authorization': authorization_header}
    return auth_header()


def verifier_eligibilite_ia(
    etudiant_id,
    type_attestation,
    inscription_validee=False,
    decision_deliberation=''
):
    """
    Appelle le service IA pour vérifier l'éligibilité.
    Retourne (eligible: bool, motif: str).
    """
    try:
        res = requests.post(
            f"{settings.SERVICE_IA}/api/evaluer/",
            json={
                'type'               : 'eligibilite_attestation',
                'etudiant'           : etudiant_id,
                'type_att'           : type_attestation,
                'inscription_validee': inscription_validee,
                'decision'           : decision_deliberation,
            },
            headers = auth_header(),
            timeout = 5
        )
        if res.status_code != 200:
            logger.warning(
                "Service IA a retourné status=%s pour etudiant=%s type=%s",
                res.status_code,
                etudiant_id,
                type_attestation,
            )
            return _eligibilite_secours(
                type_attestation,
                inscription_validee,
                decision_deliberation,
            )

        data = res.json()
        eligible = data.get('eligible')
        if eligible is None:
            return _eligibilite_secours(
                type_attestation,
                inscription_validee,
                decision_deliberation,
            )

        motif = (
            data.get('motif')
            or data.get('message')
            or data.get('detail')
            or ''
        )
        return bool(eligible), motif
    except Exception as e:
        logger.warning(f"Service IA indisponible : {e}")
        # Règle de secours locale
        return _eligibilite_secours(
            type_attestation, inscription_validee, decision_deliberation
        )


def _eligibilite_secours(type_att, inscription_validee, decision):
    """Règle de secours si le service IA est indisponible."""
    if type_att == 'inscription':
        if inscription_validee:
            return True, "Inscription validée."
        return False, "Inscription non validée."
    if type_att in ('reussite', 'passage'):
        if decision == 'admis':
            return True, "Résultat admis."
        return False, "Résultat non admis."
    if type_att in ('scolarite', 'releve_notes'):
        if inscription_validee:
            return True, "Inscription validée."
        return False, "Inscription non validée."
    return False, "Type d'attestation non reconnu."


def get_inscription_etudiant(_etudiant_id, annee, authorization_header=None):
    """
    Récupère les informations d'inscription depuis le service inscription.
    Retourne dict ou None.
    """
    try:
        res = requests.get(
            f"{settings.SERVICE_INSCRIPTION}/api/inscriptions/"
            f"mon-inscription/?annee={annee}",
            headers=forwarded_auth_header(authorization_header),
            params={'etudiant_id': _etudiant_id},
            timeout=5
        )
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        logger.warning(f"Service inscription indisponible : {e}")
        return None


def get_resultat_deliberation(_etudiant_id, annee, authorization_header=None):
    """
    Récupère les résultats de délibération depuis le service délibération.
    Retourne dict ou None.
    """
    try:
        res = requests.get(
            f"{settings.SERVICE_DELIBERATION}/api/resultats/mes-resultats/",
            headers=forwarded_auth_header(authorization_header),
            params={'etudiant_id': _etudiant_id},
            timeout=5
        )
        if res.status_code == 200:
            resultats = res.json().get('results', [])
            for r in resultats:
                if r.get('annee_universitaire') == annee:
                    return r
        return None
    except Exception as e:
        logger.warning(f"Service délibération indisponible : {e}")
        return None


def get_formation_detail(formation_id):
    """
    Récupère le détail d'une formation depuis le service dossier.
    Retourne dict ou None.
    """
    if not formation_id:
        return None

    try:
        res = requests.get(
            f"{settings.SERVICE_DOSSIER}/api/formations/{formation_id}/",
            headers=auth_header(),
            timeout=5,
        )
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        logger.warning(f"Service dossier indisponible : {e}")
        return None


def get_profil_etudiant(etudiant_id):
    """
    Récupère le profil de l'étudiant depuis le service auth.
    Utilise /api/auth/etudiants/{id}/ qui prend directement l'ID Etudiant.
    Retourne dict au format {'etudiant': {...}} ou None.
    """
    try:
        # Endpoint dédié : pk = ID de l'Etudiant (pas de l'Utilisateur)
        res = requests.get(
            f"{settings.SERVICE_AUTH}/api/auth/etudiants/{etudiant_id}/",
            headers=auth_header(),
            timeout=5
        )
        if res.status_code == 200:
            etu = res.json()
            # Retourner dans le format attendu par pdf_generator
            return {'etudiant': etu}
    except Exception as e:
        logger.warning(f"Service auth (etudiants/{etudiant_id}) indisponible : {e}")

    # Fallback : chercher via la liste des utilisateurs étudiants
    try:
        users = requests.get(
            f"{settings.SERVICE_AUTH}/api/auth/utilisateurs/?role=etudiant",
            headers=auth_header(),
            timeout=5
        )
        if users.status_code == 200:
            for item in users.json().get('results', []):
                etu = item.get('etudiant') or {}
                if etu.get('id') == etudiant_id:
                    user_id = item.get('id')
                    if not user_id:
                        return item
                    detail = requests.get(
                        f"{settings.SERVICE_AUTH}/api/auth/utilisateurs/{user_id}/",
                        headers=auth_header(),
                        timeout=5
                    )
                    if detail.status_code == 200:
                        return detail.json()
                    return item
    except Exception as e:
        logger.warning(f"Service auth (fallback liste) indisponible : {e}")

    return None


def notifier_etudiant(etudiant_id, message, canal='email'):
    """Notifie l'étudiant via le service notification."""
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
        logger.warning(f"Notification échouée pour {etudiant_id} : {e}")


def generer_numero_ordre(annee, pk):
    """Génère le numéro officiel de l'attestation."""
    return f"ATT-{annee[:4]}-{pk:06d}"
