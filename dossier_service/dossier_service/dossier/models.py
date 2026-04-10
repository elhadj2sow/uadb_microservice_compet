from django.db import models


class Formation(models.Model):
    """
    Classe Formation du diagramme de classes.
    Référentiel des formations de l'UADB.
    Référencée par tous les autres services.
    """
    NIVEAU_CHOICES = [
        ('L1', 'Licence 1'), ('L2', 'Licence 2'), ('L3', 'Licence 3'),
        ('M1', 'Master 1'),  ('M2', 'Master 2'),
        ('Doctorat', 'Doctorat'),
    ]

    code_formation  = models.CharField(
        max_length=20, unique=True,
        help_text="ex: L3-INFO, M1-SI, M2-SR"
    )
    libelle         = models.CharField(max_length=150)
    niveau          = models.CharField(max_length=10, choices=NIVEAU_CHOICES)
    specialite      = models.CharField(max_length=100, blank=True)
    departement     = models.CharField(max_length=100, blank=True)
    credits_total   = models.IntegerField(default=60)
    duree_semestres = models.IntegerField(default=2)
    actif           = models.BooleanField(default=True)
    date_creation   = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'dossier'
        db_table  = 'formation'
        ordering  = ['niveau', 'libelle']

    def __str__(self):
        return f"{self.code_formation} — {self.libelle}"


class UniteEnseignement(models.Model):
    """
    Classe UniteEnseignement du diagramme de classes.
    Référencée par deliberation.note via FK inter-services.
    """
    TYPE_CHOICES = [
        ('obligatoire', 'Obligatoire'),
        ('optionnel',   'Optionnel'),
        ('libre',       'Libre'),
    ]

    formation     = models.ForeignKey(
        Formation,
        on_delete    = models.CASCADE,
        related_name = 'unites'
    )
    code_ue       = models.CharField(
        max_length=20,
        help_text="ex: INF301, SI401"
    )
    libelle_ue    = models.CharField(max_length=150)
    semestre      = models.IntegerField(
        help_text="1, 2, 3 ou 4"
    )
    credit        = models.IntegerField(default=3)
    coefficient   = models.DecimalField(
        max_digits=3, decimal_places=1, default=1.0
    )
    type_ue       = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='obligatoire'
    )
    volume_horaire = models.IntegerField(
        null=True, blank=True,
        help_text="Heures totales"
    )
    actif         = models.BooleanField(default=True)

    class Meta:
        app_label       = 'dossier'
        db_table        = 'unite_enseignement'
        unique_together = ('formation', 'code_ue')
        ordering        = ['semestre', 'code_ue']

    def __str__(self):
        return f"{self.code_ue} — {self.libelle_ue} (S{self.semestre})"


class DossierEtudiant(models.Model):
    """
    Classe DossierEtudiant du diagramme de classes.
    Un seul dossier par étudiant et par année universitaire.
    Le score_completude est calculé automatiquement.
    """
    ETAT_CHOICES = [
        ('en_cours',   'En cours de constitution'),
        ('incomplet',  'Incomplet'),
        ('complet',    'Complet'),
        ('valide',     'Validé'),
        ('rejete',     'Rejeté'),
    ]

    etudiant_id         = models.IntegerField(
        help_text="ID de l'étudiant dans le service auth"
    )
    formation           = models.ForeignKey(
        Formation,
        on_delete = models.PROTECT,
        help_text = "Formation demandée"
    )
    annee_universitaire = models.CharField(
        max_length=10,
        help_text="ex: 2024-2025"
    )
    etat_dossier        = models.CharField(
        max_length=20,
        choices  = ETAT_CHOICES,
        default  = 'en_cours'
    )
    score_completude    = models.IntegerField(
        default   = 0,
        help_text = "0 à 100 — calculé automatiquement"
    )
    date_creation       = models.DateField(auto_now_add=True)
    date_validation     = models.DateField(null=True, blank=True)
    observation         = models.TextField(blank=True)
    valide_par          = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'agent qui a validé"
    )

    class Meta:
        app_label = 'dossier'
        db_table  = 'dossier_etudiant'
        unique_together = ('etudiant_id', 'annee_universitaire')
        ordering  = ['-date_creation']

    def __str__(self):
        return (f"Dossier étudiant {self.etudiant_id} — "
                f"{self.annee_universitaire} [{self.etat_dossier}]")

    @property
    def est_complet(self):
        return self.score_completude == 100

    @property
    def nb_pieces_deposees(self):
        return self.pieces.filter(
            statut_verification__in=('en_attente', 'valide')
        ).count()

    @property
    def nb_pieces_validees(self):
        return self.pieces.filter(
            statut_verification='valide'
        ).count()


class PieceJustificative(models.Model):
    """
    Classe PieceJustificative du diagramme de classes.
    Les fichiers sont stockés sur MinIO.
    Seul le chemin est stocké en base.
    """
    TYPE_CHOICES = [
        ('bac',                 'Baccalauréat'),
        ('cni',                 'Carte Nationale d\'Identité'),
        ('photo',               'Photo d\'identité'),
        ('diplome',             'Diplôme'),
        ('releve_notes',        'Relevé de notes'),
        ('acte_naissance',      'Acte de naissance'),
        ('certificat_medical',  'Certificat médical'),
        ('quitus_bibliotheque', 'Quitus bibliothèque'),
        ('recu_paiement',       'Reçu de paiement'),
        ('autre',               'Autre document'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente de vérification'),
        ('valide',     'Validée'),
        ('rejete',     'Rejetée'),
        ('expire',     'Expirée'),
    ]

    dossier             = models.ForeignKey(
        DossierEtudiant,
        on_delete    = models.CASCADE,
        related_name = 'pieces'
    )
    type_piece          = models.CharField(
        max_length=30, choices=TYPE_CHOICES
    )
    nom_fichier         = models.CharField(
        max_length=255,
        help_text="Nom original du fichier uploadé"
    )
    chemin_stockage     = models.CharField(
        max_length=500,
        help_text="Chemin MinIO : dossiers/{etudiant_id}/{type}/{uuid}.pdf"
    )
    taille_fichier      = models.IntegerField(
        null=True, blank=True,
        help_text="Taille en octets"
    )
    type_mime           = models.CharField(
        max_length=50, blank=True,
        help_text="application/pdf | image/jpeg | image/png"
    )
    statut_verification = models.CharField(
        max_length=20,
        choices  = STATUT_CHOICES,
        default  = 'en_attente'
    )
    motif_rejet         = models.TextField(blank=True)
    est_obligatoire     = models.BooleanField(default=True)
    date_expiration     = models.DateField(
        null=True, blank=True,
        help_text="Pour les pièces avec durée de validité"
    )
    date_depot          = models.DateTimeField(auto_now_add=True)
    date_verification   = models.DateTimeField(null=True, blank=True)
    verifie_par         = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'agent vérificateur"
    )

    class Meta:
        app_label = 'dossier'
        db_table  = 'piece_justificative'
        ordering  = ['type_piece', '-date_depot']

    def __str__(self):
        return (f"{self.get_type_piece_display()} — "
                f"Dossier {self.dossier_id} [{self.statut_verification}]")

    @property
    def est_expiree(self):
        if not self.date_expiration:
            return False
        from django.utils import timezone
        return self.date_expiration < timezone.now().date()
