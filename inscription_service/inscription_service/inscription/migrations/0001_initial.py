from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [

        # ── Créer le schéma PostgreSQL ────────────────────────
        migrations.RunSQL(
            sql    = "CREATE SCHEMA IF NOT EXISTS inscription;",
            reverse_sql = "DROP SCHEMA IF EXISTS inscription CASCADE;",
        ),

        # ── Table inscription ─────────────────────────────────
        migrations.CreateModel(
            name='Inscription',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('etudiant_id', models.IntegerField()),
                ('formation_id', models.IntegerField()),
                ('dossier_id', models.IntegerField(blank=True, null=True)),
                ('annee_universitaire', models.CharField(max_length=10)),
                ('type_inscription', models.CharField(
                    choices=[
                        ('premiere', 'Première inscription'),
                        ('reinscription', 'Réinscription')
                    ],
                    default='premiere', max_length=20
                )),
                ('statut_inscription', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('en_cours', 'En cours'),
                        ('validee', 'Validée'),
                        ('rejetee', 'Rejetée'),
                        ('annulee', 'Annulée')
                    ],
                    default='en_attente', max_length=30
                )),
                ('numero_provisoire', models.CharField(
                    blank=True, max_length=30, null=True, unique=True
                )),
                ('numero_matricule', models.CharField(
                    blank=True, max_length=30, null=True, unique=True
                )),
                ('date_preinscription', models.DateTimeField(auto_now_add=True)),
                ('date_inscription', models.DateTimeField(blank=True, null=True)),
                ('valide_par', models.IntegerField(blank=True, null=True)),
                ('observation', models.TextField(blank=True)),
            ],
            options={
                'db_table'        : 'inscription',
                'ordering'        : ['-date_preinscription'],
                'unique_together' : {('etudiant_id', 'annee_universitaire')},
            },
        ),

        # ── Table paiement ────────────────────────────────────
        migrations.CreateModel(
            name='Paiement',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('inscription', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='paiement',
                    to='inscription.inscription'
                )),
                ('montant', models.DecimalField(
                    decimal_places=2, max_digits=10
                )),
                ('montant_paye', models.DecimalField(
                    decimal_places=2, default=0, max_digits=10
                )),
                ('mode_paiement', models.CharField(
                    blank=True,
                    choices=[
                        ('especes', 'Espèces'),
                        ('virement', 'Virement bancaire'),
                        ('orange_money', 'Orange Money'),
                        ('wave', 'Wave'),
                        ('cheque', 'Chèque')
                    ],
                    max_length=30
                )),
                ('reference_paiement', models.CharField(
                    blank=True, max_length=100, null=True, unique=True
                )),
                ('statut_paiement', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('partiel', 'Partiel'),
                        ('confirme', 'Confirmé'),
                        ('rembourse', 'Remboursé')
                    ],
                    default='en_attente', max_length=20
                )),
                ('date_paiement', models.DateTimeField(blank=True, null=True)),
                ('date_confirmation', models.DateTimeField(blank=True, null=True)),
                ('confirme_par', models.IntegerField(blank=True, null=True)),
                ('recu_path', models.CharField(blank=True, max_length=255)),
            ],
            options={'db_table': 'paiement'},
        ),

        # ── Table validation_service ──────────────────────────
        migrations.CreateModel(
            name='ValidationService',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('inscription_id', models.IntegerField()),
                ('type_service', models.CharField(
                    choices=[
                        ('scolarite', 'Scolarité'),
                        ('comptabilite', 'Comptabilité / Agence comptable'),
                        ('medical', 'Service médical'),
                        ('bibliotheque', 'Bibliothèque')
                    ],
                    max_length=30
                )),
                ('statut_validation', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('en_cours', 'En cours'),
                        ('valide', 'Validé'),
                        ('rejete', 'Rejeté')
                    ],
                    default='en_attente', max_length=20
                )),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('observation', models.TextField(blank=True)),
                ('valide_par', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table'        : 'validation_service',
                'unique_together' : {('inscription_id', 'type_service')},
            },
        ),

        # ── Table workflow ────────────────────────────────────
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('inscription', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='workflow',
                    to='inscription.inscription'
                )),
                ('nom_workflow', models.CharField(
                    default='Circuit inscription administrative',
                    max_length=100
                )),
                ('description', models.TextField(blank=True)),
                ('statut', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('en_cours', 'En cours'),
                        ('termine', 'Terminé'),
                        ('annule', 'Annulé')
                    ],
                    default='en_attente', max_length=20
                )),
                ('etape_courante', models.IntegerField(default=1)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
            ],
            options={'db_table': 'workflow'},
        ),

        # ── Table etape_workflow ──────────────────────────────
        migrations.CreateModel(
            name='EtapeWorkflow',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('workflow', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='etapes',
                    to='inscription.workflow'
                )),
                ('validation_service', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='etapes',
                    to='inscription.validationservice'
                )),
                ('nom_etape', models.CharField(max_length=100)),
                ('ordre', models.IntegerField()),
                ('statut', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('en_cours', 'En cours'),
                        ('validee', 'Validée'),
                        ('rejetee', 'Rejetée')
                    ],
                    default='en_attente', max_length=20
                )),
                ('date_debut', models.DateTimeField(blank=True, null=True)),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
                ('delai_max_heures', models.IntegerField(default=48)),
                ('relances_envoyees', models.IntegerField(default=0)),
            ],
            options={
                'db_table'        : 'etape_workflow',
                'ordering'        : ['ordre'],
                'unique_together' : {('workflow', 'ordre')},
            },
        ),
    ]
