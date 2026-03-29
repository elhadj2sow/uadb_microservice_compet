from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone


def charger_roles_initiaux(apps, schema_editor):
    """Insere les 8 roles UADB au moment de la migration."""
    Role = apps.get_model('accounts', 'Role')
    roles = [
        'etudiant',
        'agent_scolarite',
        'agent_comptable',
        'service_medical',
        'bibliotheque',
        'enseignant',
        'responsable_pedagogique',
        'admin',
    ]
    for libelle in roles:
        Role.objects.get_or_create(libelle=libelle)


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [

        # ── Créer le schéma PostgreSQL ────────────────────
        migrations.RunSQL(
            sql         = "CREATE SCHEMA IF NOT EXISTS auth_uadb;",
            reverse_sql = "DROP SCHEMA IF EXISTS auth_uadb CASCADE;",
        ),

        # ── Table role ────────────────────────────────────
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('libelle', models.CharField(
                    max_length=50, unique=True
                )),
            ],
            options={
                'db_table': 'auth_uadb\".\"role',
            },
        ),

        # ── Table utilisateur ─────────────────────────────
        migrations.CreateModel(
            name='Utilisateur',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('password', models.CharField(
                    max_length=128, verbose_name='password'
                )),
                ('last_login', models.DateTimeField(
                    blank=True, null=True, verbose_name='last login'
                )),
                ('is_superuser', models.BooleanField(
                    default=False, verbose_name='superuser status'
                )),
                ('username', models.CharField(
                    error_messages={
                        'unique': 'A user with that username already exists.'
                    },
                    max_length=150,
                    unique=True,
                    validators=[
                        django.contrib.auth.validators.UnicodeUsernameValidator()
                    ],
                    verbose_name='username',
                )),
                ('first_name', models.CharField(
                    blank=True, max_length=150, verbose_name='first name'
                )),
                ('last_name', models.CharField(
                    blank=True, max_length=150, verbose_name='last name'
                )),
                ('email', models.EmailField(
                    blank=True, max_length=254, verbose_name='email address'
                )),
                ('is_staff', models.BooleanField(
                    default=False, verbose_name='staff status'
                )),
                ('is_active', models.BooleanField(
                    default=True, verbose_name='active'
                )),
                ('date_joined', models.DateTimeField(
                    default=django.utils.timezone.now,
                    verbose_name='date joined'
                )),
                ('etat_compte', models.CharField(
                    choices=[
                        ('actif', 'Actif'),
                        ('inactif', 'Inactif'),
                        ('bloque', 'Bloqué'),
                        ('suspendu', 'Suspendu'),
                    ],
                    default='actif', max_length=20
                )),
                ('groups', models.ManyToManyField(
                    blank=True,
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
                ('roles', models.ManyToManyField(
                    blank=True,
                    related_name='utilisateurs',
                    to='accounts.role',
                )),
            ],
            options={
                'db_table': 'auth_uadb\".\"utilisateur',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),

        # ── Table etudiant ────────────────────────────────
        migrations.CreateModel(
            name='Etudiant',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('utilisateur', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='etudiant',
                    to='accounts.utilisateur',
                )),
                ('matricule', models.CharField(
                    blank=True, max_length=30, null=True, unique=True
                )),
                ('ine', models.CharField(
                    blank=True, max_length=20, null=True, unique=True
                )),
                ('code_permanent', models.CharField(
                    blank=True, max_length=20, null=True, unique=True
                )),
                ('nom', models.CharField(max_length=100)),
                ('prenom', models.CharField(max_length=100)),
                ('date_naissance', models.DateField(blank=True, null=True)),
                ('lieu_naissance', models.CharField(
                    blank=True, max_length=100
                )),
                ('sexe', models.CharField(
                    blank=True,
                    choices=[('M', 'Masculin'), ('F', 'Féminin')],
                    max_length=1,
                )),
                ('telephone', models.CharField(blank=True, max_length=20)),
                ('statut', models.CharField(
                    choices=[
                        ('actif',    'Actif'),
                        ('diplome',  'Diplômé'),
                        ('abandonne','Abandonné'),
                        ('suspendu', 'Suspendu'),
                    ],
                    default='actif', max_length=20,
                )),
            ],
            options={
                'db_table': 'auth_uadb\".\"etudiant',
            },
        ),

        # ── Table journal_audit ───────────────────────────
        migrations.CreateModel(
            name='JournalAudit',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('utilisateur', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='actions_audit',
                    to='accounts.utilisateur',
                )),
                ('date_action', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(
                    choices=[
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
                    ],
                    max_length=50,
                )),
                ('ressource', models.CharField(max_length=100)),
                ('acteur', models.CharField(blank=True, max_length=150)),
                ('adresse_ip', models.CharField(blank=True, max_length=45)),
                ('user_agent', models.CharField(blank=True, max_length=255)),
                ('details', models.JSONField(blank=True, null=True)),
            ],
            options={
                'db_table': 'auth_uadb\".\"journal_audit',
                'ordering': ['-date_action'],
            },
        ),

        # ── Données initiales — 8 rôles UADB ─────────────
        migrations.RunPython(
            code         = charger_roles_initiaux,
            reverse_code = migrations.RunPython.noop,
        ),
    ]
