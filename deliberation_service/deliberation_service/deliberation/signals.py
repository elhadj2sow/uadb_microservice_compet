from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='deliberation.Note')
def recalculer_moyenne(sender, instance, **kwargs):
    """
    Déclenché à chaque sauvegarde d'une Note.
    1. Recalcule la valeur finale de la Note (CC+TP+Examen).
    2. Recalcule la moyenne du Resultat.
    3. Met à jour crédits validés et décision via règles métier.
    Correspond à est_calculé_à_partir_de du diagramme.
    """
    if instance.verrouille:
        # Ne pas recalculer si le jury est clôturé
        return

    # ── 1. Recalculer la valeur de la note ───────────────
    nouvelle_valeur = instance.calculer_valeur()
    if nouvelle_valeur != instance.valeur:
        sender.objects.filter(pk=instance.pk).update(
            valeur      = nouvelle_valeur,
            est_validee = (
                nouvelle_valeur is not None
                and nouvelle_valeur >= 10
            )
        )

    # ── 2. Recalculer la moyenne du Resultat ─────────────
    resultat = instance.resultat
    _recalculer_resultat(resultat)


def _recalculer_resultat(resultat):
    """
    Recalcule la moyenne annuelle, les crédits validés
    et propose une décision pour le Resultat.
    """
    from .models import Note, Resultat
    from .utils import appeler_moteur_regles

    notes = Note.objects.filter(
        resultat   = resultat,
        verrouille = False,
        valeur__isnull = False
    )

    if not notes.exists():
        return

    # Calcul moyenne pondérée par coefficient
    total_points     = 0
    total_coeff      = 0
    credits_valides  = 0

    for note in notes:
        coeff = float(note.coefficient_ue)
        valeur = float(note.valeur)
        total_points += valeur * coeff
        total_coeff  += coeff
        if valeur >= 10:
            credits_valides += note.credit_ue

    if total_coeff == 0:
        return

    moyenne = round(total_points / total_coeff, 2)

    # Appeler le moteur de règles (service IA ou règles secours)
    decision_data = appeler_moteur_regles(
        moyenne         = moyenne,
        credits         = credits_valides,
        etudiant_id     = resultat.etudiant_id,
        deliberation_id = resultat.deliberation_id,
    )

    Resultat.objects.filter(pk=resultat.pk).update(
        moyenne_annuelle = moyenne,
        credits_valides  = credits_valides,
        decision         = decision_data.get('decision', 'en_attente'),
        mention          = decision_data.get('mention', ''),
    )

    logger.info(
        f"Résultat {resultat.id} — étudiant {resultat.etudiant_id} "
        f"— moyenne : {moyenne} — décision : {decision_data.get('decision')}"
    )
