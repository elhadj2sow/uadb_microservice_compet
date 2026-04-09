from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

# Pièces obligatoires pour tout dossier d'inscription
PIECES_OBLIGATOIRES = [
    'bac',
    'cni',
    'photo',
    'acte_naissance',
    'certificat_medical',
    'quitus_bibliotheque',
    'recu_paiement',
]


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


@receiver(post_save, sender='dossier.PieceJustificative')
def recalculer_completude(sender, instance, **kwargs):
    """
    Déclenché à chaque dépôt ou validation de pièce.
    Recalcule le score_completude et met à jour l'état du dossier.
    Si le dossier atteint 100%, notifie l'étudiant.
    """
    from .models import DossierEtudiant

    dossier = instance.dossier

    # Pièces obligatoires validées parmi les types requis
    types_valides = list(
        dossier.pieces.filter(
            statut_verification = 'valide',
            est_obligatoire     = True,
        ).values_list('type_piece', flat=True)
    )

    nb_valides = len([
        t for t in types_valides
        if t in PIECES_OBLIGATOIRES
    ])
    nb_total = len(PIECES_OBLIGATOIRES)
    score    = int((nb_valides / nb_total) * 100)

    # Déterminer le nouvel état
    if score == 100:
        etat = 'complet'
    elif score >= 1:
        etat = 'en_cours'
    else:
        etat = 'incomplet'

    ancien_score = dossier.score_completude

    DossierEtudiant.objects.filter(pk=dossier.pk).update(
        score_completude = score,
        etat_dossier     = etat,
    )

    logger.info(
        f"Dossier {dossier.id} — score : {ancien_score}% → {score}%"
    )

    # Notifier uniquement quand le dossier passe à 100%
    if score == 100 and ancien_score < 100:
        _notifier_completude(dossier)
        _appeler_service_ia(dossier, score)


def _notifier_completude(dossier):
    """Notifie l'étudiant que son dossier est complet."""
    try:
        requests.post(
            f"{settings.SERVICE_NOTIFICATION}/api/notifications/",
            json={
                'etudiant_id': dossier.etudiant_id,
                'canal'      : 'email',
                'message'    : (
                    "Votre dossier est complet à 100%. "
                    "Vous pouvez maintenant soumettre votre "
                    "demande d'inscription administrative."
                ),
            },
            headers = auth_header(),
            timeout = 5
        )
    except Exception as e:
        logger.warning(f"Notification complétude échouée : {e}")


def _appeler_service_ia(dossier, score):
    """Informe le service IA pour traçabilité."""
    try:
        requests.post(
            f"{settings.SERVICE_IA}/api/evaluer/",
            json={
                'type'       : 'completude_dossier',
                'etudiant'   : dossier.etudiant_id,
                'dossier_id' : dossier.id,
                'score'      : score,
            },
            headers = auth_header(),
            timeout = 5
        )
    except Exception as e:
        logger.warning(f"Appel service IA échoué : {e}")
