import logging
from django.utils import timezone
from .models import Notification
from .senders import (
    envoyer_email, envoyer_sms,
    get_email_etudiant, get_telephone_etudiant
)

logger = logging.getLogger(__name__)

# Sujets par défaut selon le type
SUJETS_PAR_TYPE = {
    'inscription'  : "UADB — Mise à jour de votre inscription",
    'dossier'      : "UADB — Mise à jour de votre dossier",
    'deliberation' : "UADB — Vos résultats de délibération",
    'attestation'  : "UADB — Votre attestation est disponible",
    'workflow'     : "UADB — Action requise sur votre dossier",
    'paiement'     : "UADB — Confirmation de paiement",
    'systeme'      : "UADB — Notification",
    'chatbot'      : "UADB — Message",
}


class NotificationService:
    """
    Service principal d'envoi de notifications.
    Appelé par tous les autres microservices via l'API REST.
    """

    def envoyer(
        self,
        etudiant_id=None,
        service_destinataire=None,
        canal='email',
        message='',
        type_notification='systeme',
        sujet='',
        emetteur_service='',
        **references
    ):
        """
        Point d'entrée unique pour toutes les notifications.
        Crée la notification en base, l'envoie et met à jour son statut.

        references : inscription_id, dossier_id, deliberation_id, attestation_id
        """
        # Déterminer le sujet automatiquement si non fourni
        if not sujet:
            sujet = SUJETS_PAR_TYPE.get(type_notification, "UADB — Notification")

        # Créer la notification en base
        notif = Notification.objects.create(
            etudiant_id          = etudiant_id,
            service_destinataire = service_destinataire or '',
            type_notification    = type_notification,
            canal                = canal,
            sujet                = sujet,
            message              = message,
            emetteur_service     = emetteur_service,
            inscription_id       = references.get('inscription_id'),
            dossier_id           = references.get('dossier_id'),
            deliberation_id      = references.get('deliberation_id'),
            attestation_id       = references.get('attestation_id'),
            statut_envoi         = 'en_attente',
        )

        # Envoyer selon le canal
        succes = False
        erreur = ''

        try:
            if canal == 'email' and etudiant_id:
                succes, erreur = self._envoyer_email(
                    etudiant_id, sujet, message
                )
            elif canal == 'sms' and etudiant_id:
                succes, erreur = self._envoyer_sms(
                    etudiant_id, message
                )
            elif canal == 'interne':
                # Notification interne — juste stockée en base
                succes = True
            else:
                succes = True
                erreur = ''

        except Exception as e:
            erreur = str(e)
            logger.error(f"Erreur envoi notification {notif.id} : {e}")

        # Mettre à jour le statut
        notif.statut_envoi   = 'envoye' if succes else 'echec'
        notif.date_envoi     = timezone.now() if succes else None
        notif.erreur         = erreur
        notif.nb_tentatives += 1
        notif.save()

        return notif

    def _envoyer_email(self, etudiant_id, sujet, message):
        """Envoie un email à l'étudiant."""
        email = get_email_etudiant(etudiant_id)
        if not email:
            return False, "Email de l'étudiant non trouvé."
        html = self._generer_html(sujet, message)
        succes = envoyer_email(email, sujet, message, html)
        return succes, '' if succes else "Échec SMTP."

    def _envoyer_sms(self, etudiant_id, message):
        """Envoie un SMS à l'étudiant."""
        telephone = get_telephone_etudiant(etudiant_id)
        if not telephone:
            return False, "Téléphone de l'étudiant non trouvé."
        succes = envoyer_sms(telephone, message)
        return succes, '' if succes else "Échec SMS."

    def _generer_html(self, sujet, message):
        """Génère une version HTML simple du message email."""
        message_html = message.replace('\n', '<br>')
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px;
                     margin: 0 auto; padding: 20px;">
          <div style="background: #1a4a7a; color: white;
                      padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Université Alioune Diop de Bambey</h2>
            <p style="margin: 5px 0 0; opacity: 0.8; font-size: 14px;">
              Système d'Information Intelligent
            </p>
          </div>
          <div style="background: #f9f9f9; padding: 25px;
                      border: 1px solid #e0e0e0;">
            <h3 style="color: #1a4a7a;">{sujet}</h3>
            <p style="color: #333; line-height: 1.6;">{message_html}</p>
          </div>
          <div style="background: #eee; padding: 15px; font-size: 12px;
                      color: #666; text-align: center;
                      border-radius: 0 0 8px 8px;">
            <p>Ce message est automatique — Ne pas répondre directement.</p>
            <p>Université Alioune Diop de Bambey — Bambey, Sénégal</p>
            <p>Scolarité : +221 33 971 00 00 | scolarite@uadb.edu.sn</p>
          </div>
        </body>
        </html>
        """

    def retenter_echecs(self):
        """
        Retente l'envoi des notifications en échec.
        Appelé périodiquement ou manuellement.
        """
        echecs = Notification.objects.filter(
            statut_envoi  = 'echec',
            nb_tentatives__lt = 3
        )
        nb_reussis = 0
        for notif in echecs:
            succes = False
            if notif.canal == 'email' and notif.etudiant_id:
                email = get_email_etudiant(notif.etudiant_id)
                if email:
                    succes = envoyer_email(
                        email, notif.sujet, notif.message
                    )
            elif notif.canal == 'sms' and notif.etudiant_id:
                tel = get_telephone_etudiant(notif.etudiant_id)
                if tel:
                    succes = envoyer_sms(tel, notif.message)

            notif.nb_tentatives += 1
            if succes:
                notif.statut_envoi = 'envoye'
                notif.date_envoi   = timezone.now()
                nb_reussis += 1
            notif.save()

        logger.info(
            f"Relance notifications : {nb_reussis}/{echecs.count()} réussies"
        )
        return nb_reussis
