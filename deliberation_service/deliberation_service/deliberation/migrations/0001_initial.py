from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [

        # ── Créer le schéma PostgreSQL ────────────────────
        migrations.RunSQL(
            sql         = "CREATE SCHEMA IF NOT EXISTS deliberation;",
            reverse_sql = "DROP SCHEMA IF EXISTS deliberation CASCADE;",
        ),

        # ── Table deliberation ────────────────────────────
        migrations.CreateModel(
            name='Deliberation',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('session', models.CharField(
                    choices=[
                        ('normale',    'Session normale'),
                        ('rattrapage', 'Session de rattrapage'),
                    ],
                    default='normale', max_length=20
                )),
                ('annee_universitaire', models.CharField(max_length=10)),
                ('semestre', models.IntegerField()),
                ('niveau', models.CharField(
                    choices=[
                        ('L1','L1'),('L2','L2'),('L3','L3'),
                        ('M1','M1'),('M2','M2'),
                    ],
                    default='L1', max_length=10
                )),
                ('formation_id', models.IntegerField()),
                ('jury_president_id', models.IntegerField(
                    blank=True, null=True
                )),
                ('date_deliberation', models.DateField(
                    blank=True, null=True
                )),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_cloture', models.DateTimeField(
                    blank=True, null=True
                )),
                ('statut', models.CharField(
                    choices=[
                        ('en_preparation', 'En préparation'),
                        ('en_cours',       'En cours'),
                        ('cloturee',       'Clôturée'),
                    ],
                    default='en_preparation', max_length=20
                )),
                ('decision_finale', models.TextField(blank=True)),
                ('mention', models.CharField(blank=True, max_length=50)),
                ('observation', models.TextField(blank=True)),
            ],
            options={
                'db_table' : 'deliberation',
                'ordering' : ['-date_creation'],
                'unique_together': {(
                    'annee_universitaire',
                    'semestre',
                    'formation_id',
                    'session',
                )},
            },
        ),

        # ── Table resultat ────────────────────────────────
        migrations.CreateModel(
            name='Resultat',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('deliberation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='resultats',
                    to='deliberation.deliberation'
                )),
                ('etudiant_id', models.IntegerField()),
                ('inscription_id', models.IntegerField(
                    blank=True, null=True
                )),
                ('moyenne_s1', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('moyenne_s2', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('moyenne_annuelle', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('credits_valides', models.IntegerField(default=0)),
                ('credits_total', models.IntegerField(default=60)),
                ('decision', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('admis',      'Admis'),
                        ('rattrapage', 'Admis au rattrapage'),
                        ('ajourné',    'Ajourné'),
                        ('exclu',      'Exclu'),
                    ],
                    default='en_attente', max_length=20
                )),
                ('mention', models.CharField(
                    blank=True,
                    choices=[
                        ('',           'Sans mention'),
                        ('passable',   'Passable'),
                        ('assez_bien', 'Assez Bien'),
                        ('bien',       'Bien'),
                        ('tres_bien',  'Très Bien'),
                    ],
                    default='', max_length=20
                )),
                ('rang', models.IntegerField(blank=True, null=True)),
                ('observation', models.TextField(blank=True)),
                ('valide_par', models.IntegerField(
                    blank=True, null=True
                )),
                ('date_validation', models.DateTimeField(
                    blank=True, null=True
                )),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table'        : 'resultat',
                'ordering'        : ['rang', 'etudiant_id'],
                'unique_together' : {('deliberation', 'etudiant_id')},
            },
        ),

        # ── Table note ────────────────────────────────────
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('resultat', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notes',
                    to='deliberation.resultat'
                )),
                ('ue_id', models.IntegerField()),
                ('code_ue', models.CharField(blank=True, max_length=20)),
                ('libelle_ue', models.CharField(blank=True, max_length=150)),
                ('credit_ue', models.IntegerField(default=3)),
                ('coefficient_ue', models.DecimalField(
                    decimal_places=1, default=1.0, max_digits=3
                )),
                ('semestre', models.IntegerField(default=1)),
                ('enseignant_id', models.IntegerField(
                    blank=True, null=True
                )),
                ('note_cc', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('note_tp', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('note_examen', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('valeur', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('est_validee', models.BooleanField(default=False)),
                ('est_rattrapable', models.BooleanField(default=True)),
                ('note_rattrapage', models.DecimalField(
                    blank=True, decimal_places=2,
                    max_digits=4, null=True
                )),
                ('type_evaluation', models.CharField(
                    blank=True, max_length=30
                )),
                ('date_saisie', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('saisi_par', models.IntegerField(
                    blank=True, null=True
                )),
                ('verrouille', models.BooleanField(default=False)),
            ],
            options={
                'db_table'        : 'note',
                'ordering'        : ['semestre', 'code_ue'],
                'unique_together' : {('resultat', 'ue_id')},
            },
        ),
    ]
