from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

SERVICES_ORDRE = [
    'scolarite',
    'comptabilite',
    'medical',
    'bibliotheque',
]

NOMS_ETAPES = {
    'scolarite'   : 'Vérification scolarité',
    'comptabilite': 'Vérification paiement',
    'medical'     : 'Visite médicale',
    'bibliotheque': 'Vérification bibliothèque',
}


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
        logger.error(f"Impossible d'obtenir le token interne : {e}")
        return ''


def get_auth_header():
    token = get_internal_token()
    return {'Authorization': f'Bearer {token}'} if token else {}


def notifier_service(type_service, inscription_id, etudiant_id=None):
    """Notifie le service concerné que c'est son tour."""
    try:
        requests.post(
            f"{settings.SERVICE_NOTIFICATION}/api/notifications/",
            json={
                'service'       : type_service,
                'inscription_id': inscription_id,
                'canal'         : 'interne',
                'message'       : (
                    f"Un dossier d'inscription (ID:{inscription_id}) "
                    f"attend votre validation."
                ),
            },
            headers=get_auth_header(),
            timeout=5
        )
    except Exception as e:
        logger.warning(f"Notification service {type_service} échouée : {e}")


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
            headers=get_auth_header(),
            timeout=5
        )
    except Exception as e:
        logger.warning(f"Notification étudiant {etudiant_id} échouée : {e}")


@receiver(post_save, sender='inscription.Inscription')
def demarrer_workflow(sender, instance, created, **kwargs):
    """
    Déclenché automatiquement à la création d'une inscription.
    Implémente demarrerWorkflow() du diagramme de classes.
    Crée : numéro provisoire + 4 ValidationService + Workflow + 4 EtapeWorkflow
    """
    if not created:
        return

    from .models import ValidationService, Workflow, EtapeWorkflow

    # 1. Générer le numéro provisoire
    sender.objects.filter(pk=instance.pk).update(
        numero_provisoire  = f"PROV-{timezone.now().year}-{instance.pk:06d}",
        statut_inscription = 'en_cours',
    )
    instance.refresh_from_db()

    logger.info(
        f"Démarrage workflow inscription {instance.pk} — "
        f"étudiant {instance.etudiant_id}"
    )

    # 2. Créer les 4 ValidationService
    validations = {}
    for service in SERVICES_ORDRE:
        vs = ValidationService.objects.create(
            inscription_id    = instance.id,
            type_service      = service,
            statut_validation = 'en_attente',
        )
        validations[service] = vs

    # 3. Créer le Workflow
    wf = Workflow.objects.create(
        inscription    = instance,
        statut         = 'en_cours',
        etape_courante = 1,
    )

    # 4. Créer les 4 EtapeWorkflow
    for i, service in enumerate(SERVICES_ORDRE, start=1):
        EtapeWorkflow.objects.create(
            workflow           = wf,
            validation_service = validations[service],
            nom_etape          = NOMS_ETAPES[service],
            ordre              = i,
            statut             = 'en_cours' if i == 1 else 'en_attente',
            date_debut         = timezone.now() if i == 1 else None,
        )

    # 5. Notifier l'étudiant — préinscription reçue
    notifier_etudiant(
        instance.etudiant_id,
        f"Votre préinscription a été reçue. "
        f"Numéro provisoire : {instance.numero_provisoire}. "
        f"Le circuit de validation est en cours."
    )

    # 6. Notifier la scolarité — première étape
    notifier_service('scolarite', instance.id, instance.etudiant_id)


@receiver(post_save, sender='inscription.ValidationService')
def passer_etape_suivante(sender, instance, **kwargs):
    """
    Déclenché quand un service valide ou rejette son étape.
    Implémente passerEtapeSuivante() du diagramme de classes.
    """
    if instance.statut_validation not in ('valide', 'rejete'):
        return

    from .models import EtapeWorkflow, Inscription, Workflow

    # Trouver l'étape liée à ce ValidationService
    etape = EtapeWorkflow.objects.filter(
        validation_service=instance,
        statut='en_cours'
    ).first()

    if not etape:
        return

    wf = etape.workflow

    if instance.statut_validation == 'rejete':
        # Marquer l'étape comme rejetée
        etape.statut  = 'rejetee'
        etape.date_fin = timezone.now()
        etape.save()

        # Bloquer le workflow et l'inscription
        wf.statut = 'annule'
        wf.date_fin = timezone.now()
        wf.save()

        Inscription.objects.filter(pk=wf.inscription_id).update(
            statut_inscription='rejetee'
        )

        logger.info(
            f"Inscription {wf.inscription_id} rejetée "
            f"par {instance.type_service}"
        )
        return

    # Validation acceptée — marquer l'étape comme validée
    etape.statut  = 'validee'
    etape.date_fin = timezone.now()
    etape.save()

    # Chercher l'étape suivante
    etape_suivante = EtapeWorkflow.objects.filter(
        workflow=wf,
        ordre=etape.ordre + 1
    ).first()

    if etape_suivante:
        # Activer l'étape suivante
        etape_suivante.statut     = 'en_cours'
        etape_suivante.date_debut = timezone.now()
        etape_suivante.save()

        wf.etape_courante = etape_suivante.ordre
        wf.save()

        # Notifier le service suivant
        notifier_service(
            etape_suivante.validation_service.type_service,
            wf.inscription_id
        )

        logger.info(
            f"Inscription {wf.inscription_id} — "
            f"étape {etape.ordre} validée, "
            f"passage à l'étape {etape_suivante.ordre}"
        )
    else:
        # Toutes les étapes validées → finaliser
        finaliser_inscription(wf)


def finaliser_inscription(wf):
    """
    Toutes les étapes sont validées.
    Implémente verifierEtat() du diagramme de classes.
    Génère le matricule définitif et notifie l'étudiant.
    """
    from .models import Inscription

    wf.statut  = 'termine'
    wf.date_fin = timezone.now()
    wf.save()

    insc = wf.inscription

    # Un matricule est attribué une seule fois dans la vie de l'étudiant.
    matricule_existant = (
        Inscription.objects
        .filter(etudiant_id=insc.etudiant_id)
        .exclude(pk=insc.pk)
        .exclude(numero_matricule__isnull=True)
        .exclude(numero_matricule='')
        .order_by('date_inscription', 'id')
        .values_list('numero_matricule', flat=True)
        .first()
    )
    matricule = matricule_existant or f"UADB-{timezone.now().year}-{insc.id:06d}"

    Inscription.objects.filter(pk=insc.pk).update(
        statut_inscription = 'validee',
        numero_matricule   = matricule,
        date_inscription   = timezone.now(),
    )

    logger.info(
        f"Inscription {insc.id} finalisée — "
        f"matricule : {matricule}"
    )

    # Synchroniser le matricule vers le service auth (profil Etudiant)
    try:
        res = requests.patch(
            f"{settings.SERVICE_AUTH}/api/auth/etudiants/{insc.etudiant_id}/matricule/",
            json={'matricule': matricule},
            headers=get_auth_header(),
            timeout=5
        )
        if res.status_code >= 400:
            logger.warning(
                "Synchronisation matricule vers auth echouee "
                f"(status={res.status_code}) pour etudiant {insc.etudiant_id}: "
                f"{res.text}"
            )
    except Exception as e:
        logger.warning(
            "Erreur lors de la synchronisation matricule vers auth "
            f"pour etudiant {insc.etudiant_id}: {e}"
        )

    # Notifier l'étudiant — inscription validée
    notifier_etudiant(
        insc.etudiant_id,
        f"Félicitations ! Votre inscription est validée. "
        f"Votre numéro matricule est : {matricule}. "
        f"Vous pouvez maintenant télécharger votre attestation d'inscription."
    )
