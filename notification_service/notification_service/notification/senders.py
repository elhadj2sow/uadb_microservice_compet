import logging
import requests
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def envoyer_email(destinataire_email, sujet, message, html=None):
    """
    Envoie un email via SMTP Django.
    Retourne True si succès, False sinon.
    """
    if not destinataire_email:
        logger.warning("Email non envoyé : adresse email manquante.")
        return False
    try:
        if html:
            email = EmailMultiAlternatives(
                subject     = sujet,
                body        = message,
                from_email  = settings.DEFAULT_FROM_EMAIL,
                to          = [destinataire_email],
            )
            email.attach_alternative(html, "text/html")
            email.send()
        else:
            send_mail(
                subject       = sujet,
                message       = message,
                from_email    = settings.DEFAULT_FROM_EMAIL,
                recipient_list= [destinataire_email],
                fail_silently = False,
            )
        logger.info(f"Email envoyé à {destinataire_email} — sujet : {sujet}")
        return True
    except Exception as e:
        logger.error(f"Échec envoi email à {destinataire_email} : {e}")
        return False


def envoyer_sms(numero_telephone, message):
    """
    Envoie un SMS via l'API Orange Sénégal.
    Retourne True si succès, False sinon.
    """
    if not numero_telephone:
        logger.warning("SMS non envoyé : numéro de téléphone manquant.")
        return False

    if not settings.SMS_API_KEY or not settings.SMS_API_URL:
        logger.warning("SMS non envoyé : configuration SMS manquante.")
        return False

    # Normaliser le numéro sénégalais
    numero = _normaliser_numero(numero_telephone)
    if not numero:
        logger.warning(f"Numéro invalide : {numero_telephone}")
        return False

    try:
        headers = {
            'Authorization': f'Bearer {settings.SMS_API_KEY}',
            'Content-Type' : 'application/json',
        }
        payload = {
            'outboundSMSMessageRequest': {
                'address'                : f'tel:{numero}',
                'senderAddress'          : f'tel:{settings.SMS_SENDER}',
                'outboundSMSTextMessage' : {'message': message[:160]},
            }
        }
        res = requests.post(
            settings.SMS_API_URL,
            json    = payload,
            headers = headers,
            timeout = 10
        )
        if res.status_code in (200, 201):
            logger.info(f"SMS envoyé à {numero}")
            return True
        else:
            logger.error(
                f"Échec SMS à {numero} : "
                f"{res.status_code} — {res.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Erreur envoi SMS à {numero} : {e}")
        return False


def _normaliser_numero(numero):
    """
    Normalise un numéro de téléphone sénégalais.
    Retourne le numéro au format international ou None.
    """
    numero = numero.replace(' ', '').replace('-', '').replace('.', '')
    if numero.startswith('+221'):
        return numero
    if numero.startswith('221'):
        return f'+{numero}'
    if numero.startswith('7') and len(numero) == 9:
        return f'+221{numero}'
    if numero.startswith('0') and len(numero) == 9:
        return f'+221{numero[1:]}'
    return None


def get_email_etudiant(etudiant_id):
    """
    Récupère l'email de l'étudiant depuis le service auth.
    Retourne l'email ou None.
    """
    try:
        import requests as req
        from django.conf import settings as s
        res = req.post(
            f"{s.SERVICE_AUTH}/api/auth/login/",
            json={
                'username': s.SERVICE_INTERNAL_USER,
                'password': s.SERVICE_INTERNAL_PASSWORD,
            },
            timeout=5
        )
        token = res.json().get('access', '')
        if not token:
            return None
        headers = {'Authorization': f'Bearer {token}'}
        profil = req.get(
            f"{s.SERVICE_AUTH}/api/auth/utilisateurs/{etudiant_id}/",
            headers=headers,
            timeout=5
        )
        if profil.status_code == 200:
            payload = profil.json()
            payload_etudiant_id = payload.get('etudiant_id')
            etu = payload.get('etudiant') or {}
            if payload_etudiant_id == etudiant_id or etu.get('id') == etudiant_id:
                return payload.get('email')

        # Fallback: etudiant_id peut référencer le profil Etudiant,
        # pas l'ID Utilisateur. On cherche alors dans la liste.
        users = req.get(
            f"{s.SERVICE_AUTH}/api/auth/utilisateurs/?role=etudiant",
            headers=headers,
            timeout=5
        )
        if users.status_code == 200:
            for item in users.json().get('results', []):
                item_etudiant_id = item.get('etudiant_id')
                etu = item.get('etudiant') or {}
                if item_etudiant_id == etudiant_id or etu.get('id') == etudiant_id:
                    return item.get('email')
        return None
    except Exception as e:
        logger.warning(f"Email étudiant {etudiant_id} non récupéré : {e}")
        return None


def get_telephone_etudiant(etudiant_id):
    """
    Récupère le téléphone de l'étudiant depuis le service auth.
    Retourne le numéro ou None.
    """
    try:
        import requests as req
        from django.conf import settings as s
        res = req.post(
            f"{s.SERVICE_AUTH}/api/auth/login/",
            json={
                'username': s.SERVICE_INTERNAL_USER,
                'password': s.SERVICE_INTERNAL_PASSWORD,
            },
            timeout=5
        )
        token = res.json().get('access', '')
        if not token:
            return None
        headers = {'Authorization': f'Bearer {token}'}
        profil = req.get(
            f"{s.SERVICE_AUTH}/api/auth/utilisateurs/{etudiant_id}/",
            headers=headers,
            timeout=5
        )
        if profil.status_code == 200:
            payload = profil.json()
            payload_etudiant_id = payload.get('etudiant_id')
            etudiant = payload.get('etudiant') or {}
            if payload_etudiant_id == etudiant_id or etudiant.get('id') == etudiant_id:
                return etudiant.get('telephone')

        # Fallback si etudiant_id != utilisateur.id
        users = req.get(
            f"{s.SERVICE_AUTH}/api/auth/utilisateurs/?role=etudiant",
            headers=headers,
            timeout=5
        )
        if users.status_code == 200:
            for item in users.json().get('results', []):
                item_etudiant_id = item.get('etudiant_id')
                etu = item.get('etudiant') or {}
                if item_etudiant_id == etudiant_id or etu.get('id') == etudiant_id:
                    etudiant = item.get('etudiant') or {}
                    return etudiant.get('telephone')
        return None
    except Exception as e:
        logger.warning(f"Téléphone étudiant {etudiant_id} non récupéré : {e}")
        return None
