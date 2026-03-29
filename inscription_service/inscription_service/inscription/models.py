from django.db import models


class Inscription(models.Model):
    """
    Classe InscriptionAdministrative du diagramme de classes.
    Table centrale du service inscription.
    """
    TYPE_CHOICES = [
        ('premiere',      'Première inscription'),
        ('reinscription', 'Réinscription'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours',   'En cours'),
        ('validee',    'Validée'),
        ('rejetee',    'Rejetée'),
        ('annulee',    'Annulée'),
    ]

    etudiant_id         = models.IntegerField(
        help_text="ID de l'étudiant dans le service auth"
    )
    formation_id        = models.IntegerField(
        help_text="ID de la formation dans le service dossier"
    )
    dossier_id          = models.IntegerField(
        null=True, blank=True,
        help_text="ID du dossier dans le service dossier"
    )
    annee_universitaire = models.CharField(
        max_length=10,
        help_text="ex: 2024-2025"
    )
    type_inscription    = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='premiere'
    )
    statut_inscription  = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    numero_provisoire   = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        help_text="Attribué à la préinscription"
    )
    numero_matricule    = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        help_text="Attribué après validation complète"
    )
    date_preinscription = models.DateTimeField(auto_now_add=True)
    date_inscription    = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de validation définitive"
    )
    valide_par          = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID de l'utilisateur qui a validé"
    )
    observation         = models.TextField(blank=True)

    class Meta:
        app_label       = 'inscription'
        db_table        = 'inscription'
        unique_together = ('etudiant_id', 'annee_universitaire')
        ordering        = ['-date_preinscription']

    def __str__(self):
        return (f"Inscription {self.etudiant_id} — "
                f"{self.annee_universitaire} [{self.statut_inscription}]")


class Paiement(models.Model):
    """
    Classe Paiement du diagramme de classes.
    Liée à une inscription via OneToOne.
    """
    MODE_CHOICES = [
        ('especes',      'Espèces'),
        ('virement',     'Virement bancaire'),
        ('orange_money', 'Orange Money'),
        ('wave',         'Wave'),
        ('cheque',       'Chèque'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('partiel',    'Partiel'),
        ('confirme',   'Confirmé'),
        ('rembourse',  'Remboursé'),
    ]

    inscription         = models.OneToOneField(
        Inscription,
        on_delete=models.CASCADE,
        related_name='paiement'
    )
    montant             = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Montant total dû"
    )
    montant_paye        = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    mode_paiement       = models.CharField(
        max_length=30,
        choices=MODE_CHOICES,
        blank=True
    )
    reference_paiement  = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Référence Orange Money, numéro virement..."
    )
    statut_paiement     = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    date_paiement       = models.DateTimeField(null=True, blank=True)
    date_confirmation   = models.DateTimeField(null=True, blank=True)
    confirme_par        = models.IntegerField(null=True, blank=True)
    recu_path           = models.CharField(
        max_length=255,
        blank=True,
        help_text="Chemin MinIO vers le reçu scanné"
    )

    class Meta:
        app_label = 'inscription'
        db_table  = 'paiement'

    def __str__(self):
        return (f"Paiement inscription {self.inscription_id} — "
                f"{self.statut_paiement}")


class ValidationService(models.Model):
    """
    Classe ValidationService du diagramme de classes.
    4 lignes créées automatiquement par inscription.
    """
    SERVICE_CHOICES = [
        ('scolarite',    'Scolarité'),
        ('comptabilite', 'Comptabilité / Agence comptable'),
        ('medical',      'Service médical'),
        ('bibliotheque', 'Bibliothèque'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours',   'En cours'),
        ('valide',     'Validé'),
        ('rejete',     'Rejeté'),
    ]

    inscription_id      = models.IntegerField()
    type_service        = models.CharField(
        max_length=30,
        choices=SERVICE_CHOICES
    )
    statut_validation   = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    date_validation     = models.DateTimeField(null=True, blank=True)
    observation         = models.TextField(blank=True)
    valide_par          = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID de l'agent validant"
    )

    class Meta:
        app_label       = 'inscription'
        db_table        = 'validation_service'
        unique_together = ('inscription_id', 'type_service')

    def __str__(self):
        return (f"{self.type_service} — "
                f"Inscription {self.inscription_id} "
                f"[{self.statut_validation}]")


class Workflow(models.Model):
    """
    Classe Workflow du diagramme de classes.
    Représente le circuit numérique remplaçant la fiche papier.
    """
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours',   'En cours'),
        ('termine',    'Terminé'),
        ('annule',     'Annulé'),
    ]

    inscription         = models.OneToOneField(
        Inscription,
        on_delete=models.CASCADE,
        related_name='workflow'
    )
    nom_workflow        = models.CharField(
        max_length=100,
        default='Circuit inscription administrative'
    )
    description         = models.TextField(blank=True)
    statut              = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    etape_courante      = models.IntegerField(
        default=1,
        help_text="Numéro de l'étape en cours (1 à 4)"
    )
    date_creation       = models.DateTimeField(auto_now_add=True)
    date_fin            = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Rempli quand statut = termine"
    )

    class Meta:
        app_label = 'inscription'
        db_table  = 'workflow'

    def __str__(self):
        return (f"Workflow inscription {self.inscription_id} — "
                f"Étape {self.etape_courante}/4 [{self.statut}]")


class EtapeWorkflow(models.Model):
    """
    Classe EtapeWorkflow du diagramme de classes.
    4 étapes créées automatiquement par workflow.
    """
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours',   'En cours'),
        ('validee',    'Validée'),
        ('rejetee',    'Rejetée'),
    ]

    workflow                = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='etapes'
    )
    validation_service      = models.ForeignKey(
        ValidationService,
        on_delete=models.CASCADE,
        related_name='etapes',
        help_text="Service responsable de cette étape"
    )
    nom_etape               = models.CharField(max_length=100)
    ordre                   = models.IntegerField(
        help_text="1=scolarité, 2=comptabilité, 3=médical, 4=bibliothèque"
    )
    statut                  = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    date_debut              = models.DateTimeField(null=True, blank=True)
    date_fin                = models.DateTimeField(null=True, blank=True)
    delai_max_heures        = models.IntegerField(
        default=48,
        help_text="Délai max avant relance automatique"
    )
    relances_envoyees       = models.IntegerField(default=0)

    class Meta:
        app_label       = 'inscription'
        db_table        = 'etape_workflow'
        unique_together = ('workflow', 'ordre')
        ordering        = ['ordre']

    def __str__(self):
        return f"Étape {self.ordre} — {self.nom_etape} [{self.statut}]"
