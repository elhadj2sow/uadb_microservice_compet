from django.db import migrations, models
import django.db.models.deletion


def run_charger_base_connaissance(apps, schema_editor):
    """Deferred wrapper so function lookup happens at migration runtime."""
    return charger_base_connaissance(apps, schema_editor)


class Migration(migrations.Migration):

    initial      = True
    dependencies = []

    operations = [

        migrations.RunSQL(
            sql         = "CREATE SCHEMA IF NOT EXISTS notification;",
            reverse_sql = "DROP SCHEMA IF EXISTS notification CASCADE;",
        ),

        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('etudiant_id', models.IntegerField(blank=True, null=True)),
                ('service_destinataire', models.CharField(blank=True, max_length=50)),
                ('type_notification', models.CharField(choices=[('inscription','Inscription'),('dossier','Dossier'),('deliberation','Délibération'),('attestation','Attestation'),('workflow','Workflow'),('paiement','Paiement'),('systeme','Système'),('chatbot','Chatbot')], default='systeme', max_length=20)),
                ('canal', models.CharField(choices=[('email','Email'),('sms','SMS'),('interne','Notification interne'),('push','Push web')], default='email', max_length=20)),
                ('sujet', models.CharField(blank=True, max_length=200)),
                ('message', models.TextField()),
                ('statut_envoi', models.CharField(choices=[('en_attente','En attente'),('envoye','Envoyé'),('echec','Échec'),('lu','Lu')], default='en_attente', max_length=20)),
                ('date_notification', models.DateTimeField(auto_now_add=True)),
                ('date_envoi', models.DateTimeField(blank=True, null=True)),
                ('date_lecture', models.DateTimeField(blank=True, null=True)),
                ('erreur', models.TextField(blank=True)),
                ('emetteur_service', models.CharField(blank=True, max_length=50)),
                ('nb_tentatives', models.IntegerField(default=0)),
                ('inscription_id', models.IntegerField(blank=True, null=True)),
                ('dossier_id', models.IntegerField(blank=True, null=True)),
                ('deliberation_id', models.IntegerField(blank=True, null=True)),
                ('attestation_id', models.IntegerField(blank=True, null=True)),
            ],
            options={'db_table': 'notification', 'ordering': ['-date_notification']},
        ),

        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('etudiant_id', models.IntegerField()),
                ('statut', models.CharField(choices=[('active','Active'),('terminee','Terminée'),('archivee','Archivée')], default='active', max_length=20)),
                ('date_debut', models.DateTimeField(auto_now_add=True)),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
                ('contexte', models.JSONField(blank=True, null=True)),
                ('nb_messages', models.IntegerField(default=0)),
            ],
            options={'db_table': 'conversation', 'ordering': ['-date_debut']},
        ),

        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='notification.conversation')),
                ('contenu', models.TextField()),
                ('emetteur', models.CharField(choices=[('etudiant','Étudiant'),('chatbot','Chatbot'),('systeme','Système')], default='etudiant', max_length=20)),
                ('date_envoi', models.DateTimeField(auto_now_add=True)),
                ('intention', models.CharField(blank=True, max_length=100)),
                ('confiance', models.FloatField(blank=True, null=True)),
                ('lu', models.BooleanField(default=False)),
            ],
            options={'db_table': 'message', 'ordering': ['date_envoi']},
        ),

        migrations.CreateModel(
            name='BaseConnaissance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=200)),
                ('categorie', models.CharField(choices=[('inscription','Inscription administrative'),('dossier','Dossier étudiant'),('deliberation','Délibération et résultats'),('attestation','Attestations et documents'),('paiement','Paiement et frais'),('calendrier','Calendrier universitaire'),('contact','Contacts et services'),('general','Informations générales')], default='general', max_length=20)),
                ('questions', models.TextField()),
                ('mots_cles', models.TextField(blank=True)),
                ('contenu', models.TextField()),
                ('actif', models.BooleanField(default=True)),
                ('priorite', models.IntegerField(default=10)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_maj', models.DateField(auto_now=True)),
            ],
            options={'db_table': 'base_connaissance', 'ordering': ['priorite', 'categorie']},
        ),

        # ── Données initiales — Base de connaissance UADB ──
        migrations.RunPython(
            code         = run_charger_base_connaissance,
            reverse_code = migrations.RunPython.noop,
        ),
    ]


def charger_base_connaissance(apps, schema_editor):
    """Insère les entrées initiales de la base de connaissance."""
    BC = apps.get_model('notification', 'BaseConnaissance')

    entrees = [
        {
            'titre'    : "Comment s'inscrire à l'UADB ?",
            'categorie': 'inscription',
            'priorite' : 1,
            'questions': "comment s inscrire\ncomment faire une inscription\nprocédure inscription\nétapes inscription",
            'mots_cles': "inscription, inscrire, procédure, étapes",
            'contenu'  : (
                "Pour vous inscrire à l'UADB, suivez ces étapes :\n"
                "1. Créez votre compte sur le portail étudiant\n"
                "2. Constituez votre dossier numérique (pièces justificatives)\n"
                "3. Soumettez votre demande de préinscription\n"
                "4. Le circuit de validation démarrera automatiquement\n"
                "5. Suivez l'avancement sur votre tableau de bord\n\n"
                "Le processus passe par 4 services : Scolarité → Comptabilité → Médical → Bibliothèque."
            ),
        },
        {
            'titre'    : "Quelles pièces fournir pour le dossier ?",
            'categorie': 'dossier',
            'priorite' : 2,
            'questions': "quelles pièces fournir\ndocuments dossier\npièces justificatives\nque fournir",
            'mots_cles': "pièces, documents, dossier, justificatif, fournir",
            'contenu'  : (
                "Les pièces obligatoires pour votre dossier sont :\n"
                "• Baccalauréat (copie certifiée)\n"
                "• Carte Nationale d'Identité\n"
                "• Photo d'identité récente\n"
                "• Acte de naissance\n"
                "• Certificat médical (moins de 3 mois)\n"
                "• Quitus de la bibliothèque\n"
                "• Reçu de paiement des frais\n\n"
                "Formats acceptés : PDF, JPEG, PNG. Taille max : 5 Mo."
            ),
        },
        {
            'titre'    : "Comment consulter mes résultats ?",
            'categorie': 'deliberation',
            'priorite' : 3,
            'questions': "résultats\nnotes\nmoyenne\nbulletin\ndélibération\nadmis ou ajourné",
            'mots_cles': "résultats, notes, délibération, moyenne, admis",
            'contenu'  : (
                "Vos résultats sont disponibles après la délibération du jury :\n"
                "1. Connectez-vous sur le portail étudiant\n"
                "2. Allez dans la section 'Mes résultats'\n"
                "3. Sélectionnez l'année universitaire et le semestre\n\n"
                "Vous recevrez également une notification par email dès que les résultats sont publiés. "
                "En cas de résultat 'rattrapage', vérifiez les dates de la session de rattrapage."
            ),
        },
        {
            'titre'    : "Comment obtenir une attestation ?",
            'categorie': 'attestation',
            'priorite' : 4,
            'questions': "attestation\nobtenir attestation\ncertificat\nrelevé de notes\ndocument officiel",
            'mots_cles': "attestation, certificat, relevé, document officiel",
            'contenu'  : (
                "Pour obtenir une attestation :\n"
                "1. Connectez-vous sur le portail\n"
                "2. Allez dans 'Mes attestations'\n"
                "3. Choisissez le type : inscription, réussite, passage ou relevé de notes\n"
                "4. Soumettez votre demande\n"
                "5. Le document est généré automatiquement et disponible en PDF\n\n"
                "Types disponibles : Attestation d'inscription, de passage, de réussite, Relevé de notes, Certificat de scolarité.\n"
                "Délai : immédiat si vous êtes éligible."
            ),
        },
        {
            'titre'    : "Comment payer les frais de scolarité ?",
            'categorie': 'paiement',
            'priorite' : 5,
            'questions': "paiement\nfrais scolarité\npayer\norange money\nwave\ncombien coûte",
            'mots_cles': "paiement, frais, scolarité, orange money, wave",
            'contenu'  : (
                "Les frais de scolarité peuvent être payés par :\n"
                "• Espèces à l'agence comptable de l'UADB\n"
                "• Virement bancaire\n"
                "• Orange Money\n"
                "• Wave\n\n"
                "Conservez votre reçu de paiement et scannez-le dans votre dossier numérique. "
                "L'agence comptable confirmera le paiement dans le système."
            ),
        },
        {
            'titre'    : "Contacts de la scolarité",
            'categorie': 'contact',
            'priorite' : 6,
            'questions': "contact\ntéléphone scolarité\nemail scolarité\nadresse\nhoraires",
            'mots_cles': "contact, téléphone, email, scolarité, horaires, adresse",
            'contenu'  : (
                "Service de la Scolarité — UADB :\n"
                "• Téléphone : +221 33 971 00 00\n"
                "• Email : scolarite@uadb.edu.sn\n"
                "• Adresse : Bambey, Sénégal\n"
                "• Horaires : Lundi–Vendredi, 8h–16h30\n\n"
                "Pour les urgences, envoyez un email avec votre matricule et votre demande."
            ),
        },
        {
            'titre'    : "Suivi de mon dossier",
            'categorie': 'dossier',
            'priorite' : 7,
            'questions': "état dossier\nsuivre dossier\noù en est mon dossier\nstatut dossier",
            'mots_cles': "état, suivi, statut, dossier",
            'contenu'  : (
                "Pour suivre l'état de votre dossier :\n"
                "1. Connectez-vous sur le portail\n"
                "2. Allez dans 'Mon dossier'\n"
                "3. Consultez le score de complétude (0 à 100%)\n"
                "4. Vérifiez les pièces manquantes ou rejetées\n\n"
                "Vous recevez une notification automatique à chaque changement d'état de votre dossier."
            ),
        },
        {
            'titre'    : "Quand se déroule la rentrée universitaire ?",
            'categorie': 'calendrier',
            'priorite' : 8,
            'questions': "rentrée\ncalendrier\ndate début cours\nquand commence\nemploi du temps",
            'mots_cles': "rentrée, calendrier, date, cours, emploi du temps",
            'contenu'  : (
                "Le calendrier universitaire est disponible sur le portail de l'UADB. "
                "La rentrée officielle est généralement en octobre pour le premier semestre. "
                "Les dates précises des examens, délibérations et dépôts de dossiers sont "
                "publiées en début d'année universitaire.\n\n"
                "Consultez la section 'Calendrier' sur le portail ou contactez la scolarité."
            ),
        },
    ]

    for e in entrees:
        BC.objects.get_or_create(titre=e['titre'], defaults=e)
