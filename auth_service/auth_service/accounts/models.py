from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """
    Classe Role du diagramme de classes.
    8 rôles correspondant aux acteurs de l'UADB.
    """
    libelle = models.CharField(max_length=50, unique=True)

    class Meta:
        app_label = 'accounts'
        db_table  = 'auth_uadb\".\"role'

    def __str__(self):
        return self.libelle


class Utilisateur(AbstractUser):
    """
    Classe Utilisateur du diagramme de classes.
    Hérite de AbstractUser Django qui fournit :
    username, password (hashé), email, first_name,
    last_name, is_active, is_staff, date_joined, last_login.

    L'héritage Etudiant → Utilisateur du diagramme
    est implémenté via OneToOneField dans Etudiant.
    """
    roles = models.ManyToManyField(
        Role,
        blank        = True,
        related_name = 'utilisateurs',
    )
    etat_compte = models.CharField(
        max_length = 20,
        choices    = [
            ('actif',    'Actif'),
            ('inactif',  'Inactif'),
            ('bloque',   'Bloqué'),
            ('suspendu', 'Suspendu'),
        ],
        default = 'actif'
    )

    class Meta:
        app_label = 'accounts'
        db_table  = 'auth_uadb\".\"utilisateur'

    def __str__(self):
        return self.username

    @property
    def role_list(self):
        """Retourne la liste des rôles — utilisé dans le token JWT."""
        return list(self.roles.values_list('libelle', flat=True))

    @property
    def est_etudiant(self):
        return 'etudiant' in self.role_list

    @property
    def est_admin(self):
        return 'admin' in self.role_list


class Etudiant(models.Model):
    """
    Classe Etudiant du diagramme de classes.
    Profil universitaire séparé des données d'authentification.
    Lié à Utilisateur par OneToOneField.
    """
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete    = models.CASCADE,
        related_name = 'etudiant'
    )
    matricule = models.CharField(
        max_length = 30,
        unique     = True,
        null       = True,
        blank      = True,
        help_text  = "Attribué par le service inscription après validation"
    )
    ine = models.CharField(
        max_length = 20,
        unique     = True,
        null       = True,
        blank      = True,
        help_text  = "Identifiant National Étudiant"
    )
    code_permanent = models.CharField(
        max_length = 20,
        unique     = True,
        null       = True,
        blank      = True
    )
    nom            = models.CharField(max_length=100)
    prenom         = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=100, blank=True)
    sexe           = models.CharField(
        max_length = 1,
        choices    = [('M', 'Masculin'), ('F', 'Féminin')],
        blank      = True
    )
    telephone = models.CharField(max_length=20, blank=True)
    statut    = models.CharField(
        max_length = 20,
        choices    = [
            ('actif',    'Actif'),
            ('diplome',  'Diplômé'),
            ('abandonne','Abandonné'),
            ('suspendu', 'Suspendu'),
        ],
        default = 'actif'
    )

    class Meta:
        app_label = 'accounts'
        db_table  = 'auth_uadb\".\"etudiant'

    def __str__(self):
        return (f"{self.prenom} {self.nom} "
                f"— {self.matricule or 'sans matricule'}")

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class JournalAudit(models.Model):
    """
    Classe JournalAudit du diagramme de classes.
    Trace toutes les actions sensibles du système.
    """
    ACTION_CHOICES = [
        ('LOGIN',    'Connexion'),
        ('LOGOUT',   'Déconnexion'),
        ('CREATE',   'Création'),
        ('UPDATE',   'Modification'),
        ('DELETE',   'Suppression'),
        ('VALIDATE', 'Validation'),
        ('REJECT',   'Rejet'),
        ('GENERATE', 'Génération'),
        ('DOWNLOAD', 'Téléchargement'),
        ('RESET_PWD','Réinitialisation mot de passe'),
    ]

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete    = models.SET_NULL,
        null         = True,
        blank        = True,
        related_name = 'actions_audit'
    )
    date_action = models.DateTimeField(auto_now_add=True)
    action      = models.CharField(
        max_length = 50,
        choices    = ACTION_CHOICES
    )
    ressource   = models.CharField(
        max_length = 100,
        help_text  = "ex: auth/login, inscription/42"
    )
    acteur      = models.CharField(
        max_length = 150,
        blank      = True,
        help_text  = "Username dénormalisé pour l'historique"
    )
    adresse_ip  = models.CharField(max_length=45, blank=True)
    user_agent  = models.CharField(max_length=255, blank=True)
    details     = models.JSONField(
        null      = True,
        blank     = True,
        help_text = "Métadonnées JSON variables selon l'action"
    )

    class Meta:
        app_label = 'accounts'
        db_table  = 'auth_uadb\".\"journal_audit'
        ordering  = ['-date_action']

    def __str__(self):
        return f"{self.action} — {self.acteur} — {self.date_action}"
