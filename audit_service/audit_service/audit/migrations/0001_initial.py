from django.db import migrations, models


class Migration(migrations.Migration):

    initial      = True
    dependencies = []

    operations = [

        # ── Créer le schéma PostgreSQL ────────────────────
        migrations.RunSQL(
            sql         = "CREATE SCHEMA IF NOT EXISTS audit;",
            reverse_sql = "DROP SCHEMA IF EXISTS audit CASCADE;",
        ),

        # ── Table journal_audit ───────────────────────────
        migrations.CreateModel(
            name='JournalAudit',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('utilisateur_id',  models.IntegerField(blank=True, null=True)),
                ('acteur',          models.CharField(blank=True, max_length=150)),
                ('role_acteur',     models.CharField(blank=True, max_length=50)),
                ('action', models.CharField(
                    choices=[
                        ('LOGIN','Connexion'),
                        ('LOGOUT','Déconnexion'),
                        ('LOGIN_ECHEC','Tentative de connexion échouée'),
                        ('RESET_PWD','Réinitialisation mot de passe'),
                        ('CREATE','Création'),
                        ('UPDATE','Modification'),
                        ('DELETE','Suppression'),
                        ('READ','Consultation'),
                        ('VALIDATE','Validation'),
                        ('REJECT','Rejet'),
                        ('SUBMIT','Soumission'),
                        ('CANCEL','Annulation'),
                        ('UPLOAD','Dépôt fichier'),
                        ('DOWNLOAD','Téléchargement'),
                        ('GENERATE','Génération document'),
                        ('VERIFY','Vérification document'),
                        ('DECISION_AUTO','Décision automatique IA'),
                        ('ALERTE','Alerte anomalie'),
                        ('WORKFLOW_START','Démarrage workflow'),
                        ('WORKFLOW_STEP','Avancement étape workflow'),
                        ('WORKFLOW_END','Fin workflow'),
                        ('EXPORT','Export données'),
                        ('IMPORT','Import données'),
                        ('CONFIG','Modification configuration'),
                    ],
                    max_length=20
                )),
                ('niveau', models.CharField(
                    choices=[
                        ('INFO','Information'),
                        ('WARNING','Avertissement'),
                        ('ERROR','Erreur'),
                        ('CRITICAL','Critique'),
                    ],
                    default='INFO', max_length=10
                )),
                ('statut', models.CharField(
                    choices=[
                        ('succes','Succès'),
                        ('echec','Échec'),
                        ('partiel','Partiel'),
                    ],
                    default='succes', max_length=10
                )),
                ('description',    models.TextField(blank=True)),
                ('service',        models.CharField(blank=True, max_length=50)),
                ('ressource',      models.CharField(blank=True, max_length=200)),
                ('ressource_id',   models.IntegerField(blank=True, null=True)),
                ('ressource_type', models.CharField(blank=True, max_length=50)),
                ('etudiant_id',    models.IntegerField(blank=True, null=True)),
                ('inscription_id', models.IntegerField(blank=True, null=True)),
                ('dossier_id',     models.IntegerField(blank=True, null=True)),
                ('deliberation_id',models.IntegerField(blank=True, null=True)),
                ('attestation_id', models.IntegerField(blank=True, null=True)),
                ('adresse_ip',     models.CharField(blank=True, max_length=45)),
                ('user_agent',     models.CharField(blank=True, max_length=500)),
                ('methode_http',   models.CharField(blank=True, max_length=10)),
                ('url',            models.CharField(blank=True, max_length=500)),
                ('details',        models.JSONField(blank=True, null=True)),
                ('message_erreur', models.TextField(blank=True)),
                ('date_action',    models.DateTimeField(
                    auto_now_add=True, db_index=True
                )),
            ],
            options={
                'db_table': 'journal_audit',
                'ordering': ['-date_action'],
            },
        ),

        # ── Index pour les recherches fréquentes ──────────
        migrations.AddIndex(
            model_name='journalaudit',
            index=models.Index(
                fields=['utilisateur_id'],
                name='idx_audit_utilisateur'
            ),
        ),
        migrations.AddIndex(
            model_name='journalaudit',
            index=models.Index(
                fields=['action'],
                name='idx_audit_action'
            ),
        ),
        migrations.AddIndex(
            model_name='journalaudit',
            index=models.Index(
                fields=['service'],
                name='idx_audit_service'
            ),
        ),
        migrations.AddIndex(
            model_name='journalaudit',
            index=models.Index(
                fields=['etudiant_id'],
                name='idx_audit_etudiant'
            ),
        ),
        migrations.AddIndex(
            model_name='journalaudit',
            index=models.Index(
                fields=['niveau'],
                name='idx_audit_niveau'
            ),
        ),

        # ── Table statistique_audit ───────────────────────
        migrations.CreateModel(
            name='StatistiqueAudit',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('date',           models.DateField(unique=True)),
                ('nb_actions',     models.IntegerField(default=0)),
                ('nb_connexions',  models.IntegerField(default=0)),
                ('nb_echecs',      models.IntegerField(default=0)),
                ('nb_alertes',     models.IntegerField(default=0)),
                ('stats_services', models.JSONField(blank=True, null=True)),
                ('stats_actions',  models.JSONField(blank=True, null=True)),
                ('date_calcul',    models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'statistique_audit',
                'ordering': ['-date'],
            },
        ),
    ]
