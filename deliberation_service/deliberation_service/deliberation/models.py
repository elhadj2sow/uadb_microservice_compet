from django.db import models


class Deliberation(models.Model):
    """
    Classe Deliberation du diagramme de classes.
    Représente une session de jury pour une formation donnée.
    """
    SESSION_CHOICES = [
        ('normale',    'Session normale'),
        ('rattrapage', 'Session de rattrapage'),
    ]
    STATUT_CHOICES = [
        ('en_preparation', 'En préparation'),
        ('en_cours',       'En cours'),
        ('cloturee',       'Clôturée'),
    ]
    NIVEAU_CHOICES = [
        ('L1','L1'), ('L2','L2'), ('L3','L3'),
        ('M1','M1'), ('M2','M2'),
    ]

    session             = models.CharField(
        max_length=20,
        choices   = SESSION_CHOICES,
        default   = 'normale',
        help_text = "normale ou rattrapage"
    )
    annee_universitaire = models.CharField(
        max_length=10,
        help_text = "ex: 2024-2025"
    )
    semestre            = models.IntegerField(
        help_text="1, 2, 3 ou 4"
    )
    niveau              = models.CharField(
        max_length=10,
        choices = NIVEAU_CHOICES,
        default = 'L1'
    )
    # Références inter-services (IDs sans FK réelle)
    formation_id        = models.IntegerField(
        help_text="ID de la formation dans le service dossier"
    )
    jury_president_id   = models.IntegerField(
        null=True, blank=True,
        help_text="ID du président du jury dans le service auth"
    )
    date_deliberation   = models.DateField(null=True, blank=True)
    date_creation       = models.DateTimeField(auto_now_add=True)
    date_cloture        = models.DateTimeField(null=True, blank=True)
    statut              = models.CharField(
        max_length=20,
        choices = STATUT_CHOICES,
        default = 'en_preparation'
    )
    decision_finale     = models.TextField(blank=True)
    mention             = models.CharField(max_length=50, blank=True)
    observation         = models.TextField(blank=True)

    class Meta:
        app_label = 'deliberation'
        db_table  = 'deliberation'
        ordering  = ['-date_creation']
        unique_together = (
            'annee_universitaire',
            'semestre',
            'formation_id',
            'session'
        )

    def __str__(self):
        return (f"Délibération S{self.semestre} — "
                f"{self.annee_universitaire} — "
                f"{self.session} [{self.statut}]")


class Resultat(models.Model):
    """
    Classe Resultat du diagramme de classes.
    Une ligne par étudiant par délibération.
    Les moyennes sont calculées automatiquement
    via le signal post_save sur Note.
    """
    DECISION_CHOICES = [
        ('en_attente', 'En attente'),
        ('admis',      'Admis'),
        ('rattrapage', 'Admis au rattrapage'),
        ('ajourné',    'Ajourné'),
        ('exclu',      'Exclu'),
    ]
    MENTION_CHOICES = [
        ('',           'Sans mention'),
        ('passable',   'Passable'),
        ('assez_bien', 'Assez Bien'),
        ('bien',       'Bien'),
        ('tres_bien',  'Très Bien'),
    ]

    deliberation        = models.ForeignKey(
        Deliberation,
        on_delete    = models.CASCADE,
        related_name = 'resultats'
    )
    etudiant_id         = models.IntegerField(
        help_text="ID de l'étudiant dans le service auth"
    )
    inscription_id      = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'inscription dans le service inscription"
    )
    # Moyennes calculées automatiquement
    moyenne_s1          = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True
    )
    moyenne_s2          = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True
    )
    moyenne_annuelle    = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        help_text="Calculée automatiquement depuis les notes"
    )
    credits_valides     = models.IntegerField(default=0)
    credits_total       = models.IntegerField(default=60)
    # Décision du jury
    decision            = models.CharField(
        max_length=20,
        choices = DECISION_CHOICES,
        default = 'en_attente'
    )
    mention             = models.CharField(
        max_length=20,
        choices = MENTION_CHOICES,
        blank   = True,
        default = ''
    )
    rang                = models.IntegerField(
        null=True, blank=True
    )
    observation         = models.TextField(blank=True)
    # Traçabilité
    valide_par          = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'agent qui a validé"
    )
    date_validation     = models.DateTimeField(null=True, blank=True)
    date_creation       = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label       = 'deliberation'
        db_table        = 'resultat'
        unique_together = ('deliberation', 'etudiant_id')
        ordering        = ['rang', 'etudiant_id']

    def __str__(self):
        return (f"Résultat étudiant {self.etudiant_id} — "
                f"Délibération {self.deliberation_id} "
                f"[{self.decision}]")


class Note(models.Model):
    """
    Classe Note du diagramme de classes.
    Une ligne par UE par étudiant.
    La valeur finale est calculée automatiquement
    depuis note_cc, note_tp, note_examen.
    """
    resultat        = models.ForeignKey(
        Resultat,
        on_delete    = models.CASCADE,
        related_name = 'notes'
    )
    # Référence inter-services
    ue_id           = models.IntegerField(
        help_text="ID de l'UE dans le service dossier"
    )
    code_ue         = models.CharField(
        max_length=20, blank=True,
        help_text="Code UE dénormalisé pour affichage"
    )
    libelle_ue      = models.CharField(
        max_length=150, blank=True,
        help_text="Libellé UE dénormalisé pour affichage"
    )
    credit_ue       = models.IntegerField(
        default=3,
        help_text="Crédit de l'UE dénormalisé"
    )
    coefficient_ue  = models.DecimalField(
        max_digits=3, decimal_places=1, default=1.0
    )
    semestre        = models.IntegerField(default=1)
    enseignant_id   = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'enseignant dans le service auth"
    )
    # Notes par type d'évaluation
    note_cc         = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        help_text="Contrôle continu (30%)"
    )
    note_tp         = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        help_text="Travaux pratiques (20%)"
    )
    note_examen     = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        help_text="Examen final (50%)"
    )
    # Note finale calculée automatiquement
    valeur          = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True,
        help_text="Calculée automatiquement"
    )
    # Validation
    est_validee     = models.BooleanField(default=False)
    est_rattrapable = models.BooleanField(default=True)
    note_rattrapage = models.DecimalField(
        max_digits=4, decimal_places=2,
        null=True, blank=True
    )
    type_evaluation = models.CharField(max_length=30, blank=True)
    # Traçabilité
    date_saisie     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    saisi_par       = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'enseignant qui a saisi"
    )
    verrouille      = models.BooleanField(
        default=False,
        help_text="True après clôture jury — plus modifiable"
    )

    class Meta:
        app_label       = 'deliberation'
        db_table        = 'note'
        unique_together = ('resultat', 'ue_id')
        ordering        = ['semestre', 'code_ue']

    def __str__(self):
        return (f"Note {self.code_ue or self.ue_id} — "
                f"Étudiant {self.resultat.etudiant_id} "
                f"— {self.valeur}/20")

    def calculer_valeur(self):
        """
        Calcule la note finale de l'UE.
        CC=30%, TP=20%, Examen=50%.
        Si seulement examen : 100%.
        Si note_rattrapage fournie : valeur_finale = max(note_normale, note_rattrapage).
        """
        parties = []
        poids_total = 0

        if self.note_cc is not None:
            parties.append(float(self.note_cc) * 0.3)
            poids_total += 0.3
        if self.note_tp is not None:
            parties.append(float(self.note_tp) * 0.2)
            poids_total += 0.2
        if self.note_examen is not None:
            parties.append(float(self.note_examen) * 0.5)
            poids_total += 0.5

        note_normale = None
        if parties and poids_total > 0:
            note_normale = round(sum(parties) / poids_total, 2)

        # Prendre la meilleure note entre session normale et rattrapage
        if self.note_rattrapage is not None:
            rattrapage = float(self.note_rattrapage)
            if note_normale is not None:
                return round(max(note_normale, rattrapage), 2)
            return round(rattrapage, 2)

        return note_normale
