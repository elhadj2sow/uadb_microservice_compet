from django.db import models


class JournalAudit(models.Model):
    """
    Classe JournalAudit du diagramme de classes.
    Trace toutes les actions sensibles effectuées
    dans l'ensemble du système UADB.

    Alimenté par :
    - Le service auth (LOGIN, LOGOUT, CREATE utilisateur)
    - Le service inscription (VALIDATE, REJECT inscription)
    - Le service dossier (UPLOAD pièce, VERIFY pièce)
    - Le service délibération (SAISIR note, CLOTURER délibération)
    - Le service attestation (GENERATE, DOWNLOAD attestation)
    - Le service IA (DECISION_AUTO, ALERTE)
    - Tout autre service via l'endpoint POST /api/audit/tracer/
    """

    ACTION_CHOICES = [
        # Authentification
        ('LOGIN',           'Connexion'),
        ('LOGOUT',          'Déconnexion'),
        ('LOGIN_ECHEC',     'Tentative de connexion échouée'),
        ('RESET_PWD',       'Réinitialisation mot de passe'),
        # Gestion des données
        ('CREATE',          'Création'),
        ('UPDATE',          'Modification'),
        ('DELETE',          'Suppression'),
        ('READ',            'Consultation'),
        # Processus métier
        ('VALIDATE',        'Validation'),
        ('REJECT',          'Rejet'),
        ('SUBMIT',          'Soumission'),
        ('CANCEL',          'Annulation'),
        # Documents
        ('UPLOAD',          'Dépôt fichier'),
        ('DOWNLOAD',        'Téléchargement'),
        ('GENERATE',        'Génération document'),
        ('VERIFY',          'Vérification document'),
        # IA / Workflow
        ('DECISION_AUTO',   'Décision automatique IA'),
        ('ALERTE',          'Alerte anomalie'),
        ('WORKFLOW_START',  'Démarrage workflow'),
        ('WORKFLOW_STEP',   'Avancement étape workflow'),
        ('WORKFLOW_END',    'Fin workflow'),
        # Administration
        ('EXPORT',          'Export données'),
        ('IMPORT',          'Import données'),
        ('CONFIG',          'Modification configuration'),
    ]

    NIVEAU_CHOICES = [
        ('INFO',     'Information'),
        ('WARNING',  'Avertissement'),
        ('ERROR',    'Erreur'),
        ('CRITICAL', 'Critique'),
    ]

    STATUT_CHOICES = [
        ('succes',  'Succès'),
        ('echec',   'Échec'),
        ('partiel', 'Partiel'),
    ]

    # ── Qui ──────────────────────────────────────────────
    utilisateur_id  = models.IntegerField(
        null=True, blank=True,
        help_text="ID utilisateur dans le service auth (NULL si action système)"
    )
    acteur          = models.CharField(
        max_length=150, blank=True,
        help_text="Username dénormalisé pour l'historique"
    )
    role_acteur     = models.CharField(
        max_length=50, blank=True,
        help_text="Rôle de l'acteur au moment de l'action"
    )

    # ── Quoi ─────────────────────────────────────────────
    action          = models.CharField(
        max_length=20, choices=ACTION_CHOICES
    )
    niveau          = models.CharField(
        max_length=10, choices=NIVEAU_CHOICES, default='INFO'
    )
    statut          = models.CharField(
        max_length=10, choices=STATUT_CHOICES, default='succes'
    )
    description     = models.TextField(
        blank=True,
        help_text="Description lisible de l'action effectuée"
    )

    # ── Où (ressource concernée) ──────────────────────────
    service         = models.CharField(
        max_length=50, blank=True,
        help_text="Microservice source : auth, inscription, dossier..."
    )
    ressource       = models.CharField(
        max_length=200, blank=True,
        help_text="ex: inscription/42, dossier/15/piece/3"
    )
    ressource_id    = models.IntegerField(
        null=True, blank=True,
        help_text="ID de la ressource concernée"
    )
    ressource_type  = models.CharField(
        max_length=50, blank=True,
        help_text="Type : Inscription, Dossier, Note, Attestation..."
    )

    # ── Références inter-services ─────────────────────────
    etudiant_id     = models.IntegerField(null=True, blank=True)
    inscription_id  = models.IntegerField(null=True, blank=True)
    dossier_id      = models.IntegerField(null=True, blank=True)
    deliberation_id = models.IntegerField(null=True, blank=True)
    attestation_id  = models.IntegerField(null=True, blank=True)

    # ── Contexte technique ────────────────────────────────
    adresse_ip      = models.CharField(max_length=45, blank=True)
    user_agent      = models.CharField(max_length=500, blank=True)
    methode_http    = models.CharField(
        max_length=10, blank=True,
        help_text="GET, POST, PATCH, DELETE"
    )
    url             = models.CharField(max_length=500, blank=True)
    details         = models.JSONField(
        null=True, blank=True,
        help_text="Données supplémentaires spécifiques à l'action"
    )
    message_erreur  = models.TextField(
        blank=True,
        help_text="Message d'erreur si statut = echec"
    )

    # ── Quand ─────────────────────────────────────────────
    date_action     = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        app_label = 'audit'
        db_table  = 'journal_audit'
        ordering  = ['-date_action']
        indexes   = [
            models.Index(fields=['utilisateur_id']),
            models.Index(fields=['action']),
            models.Index(fields=['service']),
            models.Index(fields=['etudiant_id']),
            models.Index(fields=['date_action']),
            models.Index(fields=['niveau']),
        ]

    def __str__(self):
        return (
            f"[{self.service}] {self.action} — "
            f"{self.acteur or 'système'} — "
            f"{self.date_action.strftime('%d/%m/%Y %H:%M')}"
        )


class StatistiqueAudit(models.Model):
    """
    Statistiques pré-calculées du journal d'audit.
    Mise à jour quotidiennement pour les tableaux de bord.
    Évite de recalculer sur des millions de lignes à chaque requête.
    """
    date        = models.DateField(unique=True)
    nb_actions  = models.IntegerField(default=0)
    nb_connexions  = models.IntegerField(default=0)
    nb_echecs   = models.IntegerField(default=0)
    nb_alertes  = models.IntegerField(default=0)
    # Par service
    stats_services = models.JSONField(
        null=True, blank=True,
        help_text="Nombre d'actions par service"
    )
    # Par action
    stats_actions  = models.JSONField(
        null=True, blank=True,
        help_text="Nombre d'occurrences par action"
    )
    date_calcul = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'audit'
        db_table  = 'statistique_audit'
        ordering  = ['-date']

    def __str__(self):
        return f"Stats audit {self.date} — {self.nb_actions} actions"
