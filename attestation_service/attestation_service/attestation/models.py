from django.db import models
import uuid


class DemandeAttestation(models.Model):
    """
    Classe DemandeAttestation du diagramme de classes.
    Soumise par l'étudiant — traitée automatiquement
    par le moteur de règles du service IA.
    """
    TYPE_CHOICES = [
        ('inscription', "Attestation d'inscription"),
        ('passage',     'Attestation de passage'),
        ('reussite',    'Attestation de réussite'),
        ('releve_notes','Relevé de notes'),
        ('scolarite',   'Certificat de scolarité'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuvee',  'Approuvée'),
        ('refusee',    'Refusée'),
        ('generee',    'Générée'),
    ]

    etudiant_id         = models.IntegerField(
        help_text="ID de l'étudiant dans le service auth"
    )
    type_attestation    = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )
    annee_universitaire = models.CharField(
        max_length=10,
        blank=True,
        help_text="ex: 2024-2025"
    )
    motif               = models.TextField(
        blank=True,
        help_text="Raison de la demande : bourse, stage, concours..."
    )
    statut              = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    # Résultat du moteur de règles (service IA)
    decision_ia         = models.CharField(
        max_length=20,
        blank=True,
        help_text="eligible | non_eligible — résultat du MoteurDecision"
    )
    motif_refus         = models.TextField(
        blank=True,
        help_text="Rempli si statut = refusee"
    )
    # Références inter-services
    inscription_id      = models.IntegerField(
        null=True, blank=True,
        help_text="ID inscription dans le service inscription"
    )
    deliberation_id     = models.IntegerField(
        null=True, blank=True,
        help_text="ID délibération dans le service délibération"
    )
    # Traçabilité
    date_demande        = models.DateTimeField(auto_now_add=True)
    date_traitement     = models.DateTimeField(null=True, blank=True)
    traite_par          = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'agent — NULL si traitement automatique"
    )

    class Meta:
        app_label = 'attestation'
        db_table  = 'demande_attestation'
        ordering  = ['-date_demande']

    def __str__(self):
        return (
            f"Demande {self.get_type_attestation_display()} "
            f"— étudiant {self.etudiant_id} [{self.statut}]"
        )


class Attestation(models.Model):
    """
    Classe Attestation du diagramme de classes.
    Générée automatiquement après approbation de la demande.
    Le PDF est stocké sur MinIO.
    Le code_verification permet l'authentification publique du document.
    """
    STATUT_CHOICES = [
        ('generee',  'Générée'),
        ('delivree', 'Délivrée'),
        ('annulee',  'Annulée'),
    ]

    demande             = models.OneToOneField(
        DemandeAttestation,
        on_delete    = models.CASCADE,
        related_name = 'attestation'
    )
    type_attestation    = models.CharField(max_length=20)
    annee_universitaire = models.CharField(max_length=10, blank=True)

    # Numérotation officielle
    numero_ordre        = models.CharField(
        max_length=30,
        unique=True,
        help_text="ex: ATT-2025-000123"
    )
    # Authentification publique
    code_verification   = models.CharField(
        max_length=64,
        unique=True,
        default=uuid.uuid4,
        help_text="UUID intégré dans le QR code"
    )
    # Fichiers stockés sur MinIO
    pdf_path            = models.CharField(
        max_length=500,
        blank=True,
        help_text="attestations/2025/ATT-2025-000123.pdf"
    )
    qr_code_path        = models.CharField(
        max_length=500,
        blank=True,
        help_text="qrcodes/2025/ATT-2025-000123.png"
    )
    # Statut
    statut_attestation  = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='generee'
    )
    signature_electronique = models.BooleanField(default=True)
    signe_par           = models.IntegerField(
        null=True, blank=True,
        help_text="ID du signataire — NULL si signature auto"
    )
    # Dates
    date_generation     = models.DateTimeField(auto_now_add=True)
    date_retrait        = models.DateTimeField(
        null=True, blank=True,
        help_text="Date de premier téléchargement"
    )

    class Meta:
        app_label = 'attestation'
        db_table  = 'attestation'
        ordering  = ['-date_generation']

    def __str__(self):
        return (
            f"{self.numero_ordre} — "
            f"étudiant {self.demande.etudiant_id} "
            f"[{self.statut_attestation}]"
        )
