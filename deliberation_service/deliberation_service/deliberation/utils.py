import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_internal_token():
    """Token JWT pour les appels inter-services."""
    try:
        res = requests.post(
            f"{settings.SERVICE_AUTH}/api/auth/login/",
            json={
                'username': settings.SERVICE_INTERNAL_USER,
                'password': settings.SERVICE_INTERNAL_PASSWORD,
            },
            timeout=5
        )
        return res.json().get('access', '')
    except Exception as e:
        logger.warning(f"Token interne non obtenu : {e}")
        return ''


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
        return res.json()
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
