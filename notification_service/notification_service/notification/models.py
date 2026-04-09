from django.db import models


class Notification(models.Model):
    """
    Classe Notification du diagramme de classes.
    Trace chaque notification envoyée à un étudiant
    ou un service depuis n'importe quel microservice.
    """
    CANAL_CHOICES = [
        ('email',   'Email'),
        ('sms',     'SMS'),
        ('interne', 'Notification interne'),
        ('push',    'Push web'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('envoye',     'Envoyé'),
        ('echec',      'Échec'),
        ('lu',         'Lu'),
    ]
    TYPE_CHOICES = [
        ('inscription',   'Inscription'),
        ('dossier',       'Dossier'),
        ('deliberation',  'Délibération'),
        ('attestation',   'Attestation'),
        ('workflow',      'Workflow'),
        ('paiement',      'Paiement'),
        ('systeme',       'Système'),
        ('chatbot',       'Chatbot'),
    ]

    # Destinataire
    etudiant_id         = models.IntegerField(
        null=True, blank=True,
        help_text="ID étudiant dans le service auth"
    )
    service_destinataire = models.CharField(
        max_length=50, blank=True,
        help_text="scolarite | comptabilite | medical | bibliotheque"
    )
    # Contenu
    type_notification   = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='systeme'
    )
    canal               = models.CharField(
        max_length=20,
        choices=CANAL_CHOICES,
        default='email'
    )
    sujet               = models.CharField(
        max_length=200,
        blank=True,
        help_text="Objet de l'email"
    )
    message             = models.TextField()
    # Références inter-services
    inscription_id      = models.IntegerField(null=True, blank=True)
    dossier_id          = models.IntegerField(null=True, blank=True)
    deliberation_id     = models.IntegerField(null=True, blank=True)
    attestation_id      = models.IntegerField(null=True, blank=True)
    # Statut
    statut_envoi        = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente'
    )
    date_notification   = models.DateTimeField(auto_now_add=True)
    date_envoi          = models.DateTimeField(null=True, blank=True)
    date_lecture        = models.DateTimeField(null=True, blank=True)
    erreur              = models.TextField(
        blank=True,
        help_text="Message d'erreur si envoi échoué"
    )
    # Traçabilité
    emetteur_service    = models.CharField(
        max_length=50, blank=True,
        help_text="Service qui a déclenché la notification"
    )
    nb_tentatives       = models.IntegerField(default=0)

    class Meta:
        app_label = 'notification'
        db_table  = 'notification'
        ordering  = ['-date_notification']

    def __str__(self):
        dest = (
            f"étudiant {self.etudiant_id}"
            if self.etudiant_id
            else f"service {self.service_destinataire}"
        )
        return (
            f"[{self.canal}] {self.type_notification} → "
            f"{dest} [{self.statut_envoi}]"
        )


class Conversation(models.Model):
    """
    Classe Conversation du diagramme de classes.
    Représente une session de chat entre un étudiant
    et le chatbot d'assistance.
    """
    STATUT_CHOICES = [
        ('active',   'Active'),
        ('terminee', 'Terminée'),
        ('archivee', 'Archivée'),
    ]

    etudiant_id = models.IntegerField(
        help_text="ID de l'étudiant dans le service auth"
    )
    statut      = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='active'
    )
    date_debut  = models.DateTimeField(auto_now_add=True)
    date_fin    = models.DateTimeField(null=True, blank=True)
    # Contexte de la conversation
    contexte    = models.JSONField(
        null=True, blank=True,
        help_text="Données de contexte (formation, inscription...)"
    )
    nb_messages = models.IntegerField(default=0)

    class Meta:
        app_label = 'notification'
        db_table  = 'conversation'
        ordering  = ['-date_debut']

    def __str__(self):
        return (
            f"Conversation étudiant {self.etudiant_id} "
            f"— {self.date_debut.strftime('%d/%m/%Y %H:%M')} "
            f"[{self.statut}]"
        )


class Message(models.Model):
    """
    Classe Message du diagramme de classes.
    Un message dans une conversation chatbot.
    """
    EMETTEUR_CHOICES = [
        ('etudiant', 'Étudiant'),
        ('chatbot',  'Chatbot'),
        ('systeme',  'Système'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete    = models.CASCADE,
        related_name = 'messages'
    )
    contenu      = models.TextField()
    emetteur     = models.CharField(
        max_length=20,
        choices=EMETTEUR_CHOICES,
        default='etudiant'
    )
    date_envoi   = models.DateTimeField(auto_now_add=True)
    # Métadonnées chatbot
    intention    = models.CharField(
        max_length=100, blank=True,
        help_text="Intention détectée par le chatbot"
    )
    confiance    = models.FloatField(
        null=True, blank=True,
        help_text="Score de confiance 0.0 à 1.0"
    )
    lu           = models.BooleanField(default=False)

    class Meta:
        app_label = 'notification'
        db_table  = 'message'
        ordering  = ['date_envoi']

    def __str__(self):
        return (
            f"[{self.emetteur}] {self.contenu[:50]}... "
            f"— {self.date_envoi.strftime('%H:%M')}"
        )


class BaseConnaissance(models.Model):
    """
    Classe BaseConnaissance du diagramme de classes.
    Base de connaissances utilisée par le chatbot
    pour répondre aux questions fréquentes.
    """
    CATEGORIE_CHOICES = [
        ('inscription',  'Inscription administrative'),
        ('dossier',      'Dossier étudiant'),
        ('deliberation', 'Délibération et résultats'),
        ('attestation',  'Attestations et documents'),
        ('paiement',     'Paiement et frais'),
        ('calendrier',   'Calendrier universitaire'),
        ('contact',      'Contacts et services'),
        ('general',      'Informations générales'),
    ]

    titre     = models.CharField(max_length=200)
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIE_CHOICES,
        default='general'
    )
    # Questions déclencheurs (une par ligne)
    questions = models.TextField(
        help_text="Questions déclencheurs — une par ligne"
    )
    # Mots-clés pour la recherche
    mots_cles = models.TextField(
        blank=True,
        help_text="Mots-clés séparés par des virgules"
    )
    contenu   = models.TextField(
        help_text="Réponse du chatbot"
    )
    actif     = models.BooleanField(default=True)
    priorite  = models.IntegerField(
        default=10,
        help_text="Plus petit = priorité plus haute"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj      = models.DateField(auto_now=True)

    class Meta:
        app_label = 'notification'
        db_table  = 'base_connaissance'
        ordering  = ['priorite', 'categorie']

    def __str__(self):
        return f"[{self.categorie}] {self.titre}"

    @property
    def liste_questions(self):
        return [q.strip() for q in self.questions.split('\n') if q.strip()]

    @property
    def liste_mots_cles(self):
        return [m.strip() for m in self.mots_cles.split(',') if m.strip()]
