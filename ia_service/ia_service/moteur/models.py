from django.db import models


class RegleMetier(models.Model):
    """
    Classe RegleMetier du diagramme de classes.
    Règles stockées en base → modifiables sans redéployer le code.
    La condition est une expression Python évaluable.
    """
    DOMAINE_CHOICES = [
        ('dossier',      'Dossier étudiant'),
        ('inscription',  'Inscription administrative'),
        ('deliberation', 'Délibération'),
        ('attestation',  'Attestation'),
        ('workflow',     'Workflow'),
    ]

    code_regle  = models.CharField(
        max_length=60, unique=True,
        help_text="ex: DOSSIER_COMPLETUDE, DELIB_ADMISSION"
    )
    libelle     = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    domaine     = models.CharField(
        max_length=20, choices=DOMAINE_CHOICES
    )
    condition   = models.TextField(
        help_text=(
            "Expression Python évaluable avec contexte['...'].\n"
            "ex: contexte['score'] == 100\n"
            "ex: contexte['moyenne'] >= 10 and contexte['credits'] >= 60"
        )
    )
    action      = models.CharField(
        max_length=50,
        help_text="Résultat si condition vraie. ex: eligible, admis, complet"
    )
    priorite    = models.IntegerField(
        default=10,
        help_text="Ordre d'évaluation — plus petit = évalué en premier"
    )
    active      = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj      = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'moteur'
        db_table  = 'regle_metier'
        ordering  = ['priorite', 'domaine']

    def __str__(self):
        return f"[{self.domaine}] {self.code_regle} — {self.libelle}"


class MoteurDecision(models.Model):
    """
    Classe MoteurDecision du diagramme de classes.
    Instance singleton représentant le moteur.
    Implémente evaluerRegles() et produireDecision().
    """
    nom     = models.CharField(max_length=100, default='Moteur UADB v1')
    version = models.CharField(max_length=20,  default='1.0.0')
    statut  = models.CharField(
        max_length=20,
        choices=[('actif','Actif'),('inactif','Inactif')],
        default='actif'
    )
    regles  = models.ManyToManyField(
        RegleMetier,
        blank=True,
        related_name='moteurs'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'moteur'
        db_table  = 'moteur_decision'

    def __str__(self):
        return f"{self.nom} v{self.version} [{self.statut}]"


class DecisionAutomatique(models.Model):
    """
    Classe DecisionAutomatique du diagramme de classes.
    Trace chaque décision prise par le moteur.
    Permet la traçabilité complète des décisions IA.
    """
    TYPE_CHOICES = [
        ('completude_dossier',     'Complétude dossier'),
        ('eligibilite_inscription','Éligibilité inscription'),
        ('validation_deliberation','Validation délibération'),
        ('eligibilite_attestation','Éligibilité attestation'),
        ('detection_anomalie',     'Détection anomalie'),
    ]

    type_decision    = models.CharField(
        max_length=30, choices=TYPE_CHOICES
    )
    date_decision    = models.DateTimeField(auto_now_add=True)
    resultat         = models.CharField(
        max_length=30,
        help_text="eligible, non_eligible, admis, ajourné, complet..."
    )
    motif            = models.TextField(
        blank=True,
        help_text="Explication lisible de la décision"
    )
    niveau_confiance = models.FloatField(
        default=1.0,
        help_text="0.0 à 1.0"
    )
    regle_appliquee  = models.ForeignKey(
        RegleMetier,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='decisions',
        help_text="Règle qui a déclenché cette décision"
    )
    # Références inter-services (IDs sans FK réelle)
    etudiant_id      = models.IntegerField(null=True, blank=True)
    dossier_id       = models.IntegerField(null=True, blank=True)
    inscription_id   = models.IntegerField(null=True, blank=True)
    deliberation_id  = models.IntegerField(null=True, blank=True)
    demande_id       = models.IntegerField(null=True, blank=True)
    # Contexte d'évaluation (données soumises)
    contexte_json    = models.JSONField(
        null=True, blank=True,
        help_text="Données soumises au moteur"
    )

    class Meta:
        app_label = 'moteur'
        db_table  = 'decision_automatique'
        ordering  = ['-date_decision']

    def __str__(self):
        return (
            f"[{self.type_decision}] {self.resultat} "
            f"— étudiant {self.etudiant_id} "
            f"— {self.date_decision.strftime('%d/%m/%Y %H:%M')}"
        )


class AlerteAnomalie(models.Model):
    """
    Classe AlerteAnomalie du diagramme de classes.
    Signale une anomalie détectée par le moteur.
    Absente du diagramme final section 10 — ajoutée ici
    conformément à la section 9.
    """
    TYPE_CHOICES = [
        ('dossier_incomplet', 'Dossier incomplet depuis trop longtemps'),
        ('piece_expiree',     'Pièce justificative expirée'),
        ('note_aberrante',    'Note aberrante détectée'),
        ('doublon',           'Doublon détecté'),
        ('delai_depasse',     'Délai de traitement dépassé'),
        ('incoherence',       'Incohérence dans les données'),
    ]
    GRAVITE_CHOICES = [
        ('faible',   'Faible'),
        ('moyenne',  'Moyenne'),
        ('elevee',   'Élevée'),
        ('critique', 'Critique'),
    ]
    STATUT_CHOICES = [
        ('ouverte',   'Ouverte'),
        ('en_cours',  'En cours de traitement'),
        ('resolue',   'Résolue'),
        ('ignoree',   'Ignorée'),
    ]

    type_alerte       = models.CharField(
        max_length=30, choices=TYPE_CHOICES
    )
    date_detection    = models.DateTimeField(auto_now_add=True)
    niveau_gravite    = models.CharField(
        max_length=20, choices=GRAVITE_CHOICES, default='moyenne'
    )
    description       = models.TextField()
    statut_traitement = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='ouverte'
    )
    date_resolution   = models.DateTimeField(null=True, blank=True)
    resolu_par        = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'agent ayant résolu l'alerte"
    )
    note_resolution   = models.TextField(blank=True)
    # Références inter-services
    etudiant_id       = models.IntegerField(null=True, blank=True)
    dossier_id        = models.IntegerField(null=True, blank=True)
    inscription_id    = models.IntegerField(null=True, blank=True)
    deliberation_id   = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = 'moteur'
        db_table  = 'alerte_anomalie'
        ordering  = ['-date_detection']

    def __str__(self):
        return (
            f"[{self.niveau_gravite}] {self.type_alerte} "
            f"— étudiant {self.etudiant_id} "
            f"[{self.statut_traitement}]"
        )
