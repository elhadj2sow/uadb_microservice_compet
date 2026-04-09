import logging
from django.utils import timezone
from django.conf import settings

from .models import DemandeAttestation, Attestation
from .storage import stocker_pdf, stocker_image, generer_url_telechargement
from .pdf_generator import (
    generer_pdf_attestation,
    generer_pdf_releve_notes,
    generer_qr_code,
)
from .utils import (
    verifier_eligibilite_ia,
    get_inscription_etudiant,
    get_resultat_deliberation,
    get_profil_etudiant,
    notifier_etudiant,
    generer_numero_ordre,
)

logger = logging.getLogger(__name__)


class AttestationService:
    """
    Service principal orchestrant le pipeline complet :
    1. Vérifier éligibilité (service IA)
    2. Générer QR code
    3. Générer PDF
    4. Stocker sur MinIO
    5. Enregistrer en base
    6. Notifier l'étudiant
    """

    def traiter_demande(self, demande: DemandeAttestation, authorization_header=None):
        """
        Pipeline complet de traitement d'une demande.
        Retourne l'Attestation créée ou None si refusée.
        """
        logger.info(
            f"Traitement demande {demande.id} — "
            f"étudiant {demande.etudiant_id} — "
            f"type {demande.type_attestation}"
        )

        # ── 1. Collecter les données inter-services ───────
        annee = demande.annee_universitaire
        inscription   = get_inscription_etudiant(
            demande.etudiant_id, annee, authorization_header
        )
        deliberation  = get_resultat_deliberation(
            demande.etudiant_id, annee, authorization_header
        )
        profil        = get_profil_etudiant(demande.etudiant_id)

        inscription_validee   = (
            inscription is not None
            and inscription.get('statut_inscription') == 'validee'
        )
        decision_deliberation = (
            deliberation.get('decision', '')
            if deliberation else ''
        )

        # ── 2. Vérifier éligibilité via service IA ────────
        eligible, motif = verifier_eligibilite_ia(
            etudiant_id          = demande.etudiant_id,
            type_attestation     = demande.type_attestation,
            inscription_validee  = inscription_validee,
            decision_deliberation= decision_deliberation,
        )

        if not eligible:
            motif = motif or "Non éligible selon les règles d'attestation."
            # Refuser la demande
            demande.statut        = 'refusee'
            demande.decision_ia   = 'non_eligible'
            demande.motif_refus   = motif
            demande.date_traitement = timezone.now()
            demande.save()

            notifier_etudiant(
                demande.etudiant_id,
                f"Votre demande d'attestation "
                f"({demande.get_type_attestation_display()}) "
                f"a été refusée. Motif : {motif}"
            )
            logger.info(
                f"Demande {demande.id} refusée : {motif}"
            )
            return None

        # ── 3. Créer l'Attestation en base (pour obtenir l'ID) ──
        demande.statut      = 'approuvee'
        demande.decision_ia = 'eligible'
        if inscription:
            demande.inscription_id = inscription.get('id')
        if deliberation:
            demande.deliberation_id = deliberation.get('id')
        demande.save()

        attestation = Attestation.objects.create(
            demande             = demande,
            type_attestation    = demande.type_attestation,
            annee_universitaire = annee,
            numero_ordre        = 'TEMP',  # sera mis à jour après
        )

        # Mettre à jour le numéro officiel
        numero = generer_numero_ordre(annee or str(timezone.now().year), attestation.pk)
        attestation.numero_ordre = numero
        attestation.save()

        # ── 4. Générer le QR code ─────────────────────────
        qr_buf  = generer_qr_code(str(attestation.code_verification))
        qr_path = (
            f"qrcodes/{timezone.now().year}/"
            f"{numero}.png"
        )
        stocker_image(qr_buf, qr_path)
        attestation.qr_code_path = qr_path

        # ── 5. Générer le PDF ─────────────────────────────
        if demande.type_attestation == 'releve_notes' and deliberation:
            notes_data = deliberation.get('notes', [])
            pdf_buf = generer_pdf_releve_notes(
                demande,
                attestation,
                notes_data,
                profil,
                deliberation,
            )
        else:
            pdf_buf = generer_pdf_attestation(
                demande, attestation, profil
            )

        if not pdf_buf:
            logger.error(f"Échec génération PDF pour demande {demande.id}")
            attestation.delete()
            demande.statut = 'en_attente'
            demande.save()
            return None

        # ── 6. Stocker le PDF sur MinIO ───────────────────
        pdf_path = (
            f"attestations/{timezone.now().year}/"
            f"{numero}.pdf"
        )
        if not stocker_pdf(pdf_buf, pdf_path):
            logger.error(f"Échec stockage PDF pour demande {demande.id}")
            attestation.delete()
            demande.statut = 'en_attente'
            demande.save()
            return None

        # ── 7. Finaliser l'attestation ────────────────────
        attestation.pdf_path  = pdf_path
        attestation.save()

        demande.statut          = 'generee'
        demande.date_traitement = timezone.now()
        demande.save()

        # ── 8. Notifier l'étudiant ────────────────────────
        notifier_etudiant(
            demande.etudiant_id,
            f"Votre {demande.get_type_attestation_display()} "
            f"(N° {numero}) est disponible. "
            f"Connectez-vous sur le portail pour la télécharger."
        )

        logger.info(
            f"Attestation {numero} générée pour "
            f"étudiant {demande.etudiant_id}"
        )
        return attestation
