from django.db import migrations, models
import django.db.models.deletion


def charger_formations_initiales(apps, schema_editor):
    """Insère les formations de l'UADB au moment de la migration."""
    Formation = apps.get_model('dossier', 'Formation')
    UniteEnseignement = apps.get_model('dossier', 'UniteEnseignement')

    formations_data = [
        {
            'code_formation' : 'L3-INFO',
            'libelle'        : 'Licence 3 Informatique',
            'niveau'         : 'L3',
            'specialite'     : 'Informatique',
            'departement'    : 'UFR SATIC',
            'credits_total'  : 60,
            'duree_semestres': 2,
        },
        {
            'code_formation' : 'M1-SI',
            'libelle'        : "Master 1 Systèmes d'Information",
            'niveau'         : 'M1',
            'specialite'     : "Systèmes d'Information",
            'departement'    : 'UFR SATIC',
            'credits_total'  : 60,
            'duree_semestres': 2,
        },
        {
            'code_formation' : 'M2-SI',
            'libelle'        : "Master 2 Systèmes d'Information",
            'niveau'         : 'M2',
            'specialite'     : "Systèmes d'Information",
            'departement'    : 'UFR SATIC',
            'credits_total'  : 60,
            'duree_semestres': 2,
        },
        {
            'code_formation' : 'M1-SR',
            'libelle'        : 'Master 1 Systèmes et Réseaux',
            'niveau'         : 'M1',
            'specialite'     : 'Réseaux',
            'departement'    : 'UFR SATIC',
            'credits_total'  : 60,
            'duree_semestres': 2,
        },
        {
            'code_formation' : 'M2-SR',
            'libelle'        : 'Master 2 Systèmes et Réseaux',
            'niveau'         : 'M2',
            'specialite'     : 'Réseaux',
            'departement'    : 'UFR SATIC',
            'credits_total'  : 60,
            'duree_semestres': 2,
        },
    ]

    for fdata in formations_data:
        Formation.objects.get_or_create(
            code_formation=fdata['code_formation'],
            defaults=fdata
        )


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [

        # ── Créer le schéma PostgreSQL ────────────────────
        migrations.RunSQL(
            sql         = "CREATE SCHEMA IF NOT EXISTS dossier;",
            reverse_sql = "DROP SCHEMA IF EXISTS dossier CASCADE;",
        ),

        # ── Table formation ───────────────────────────────
        migrations.CreateModel(
            name='Formation',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('code_formation', models.CharField(
                    max_length=20, unique=True
                )),
                ('libelle', models.CharField(max_length=150)),
                ('niveau', models.CharField(
                    choices=[
                        ('L1','Licence 1'),('L2','Licence 2'),
                        ('L3','Licence 3'),('M1','Master 1'),
                        ('M2','Master 2'),('Doctorat','Doctorat'),
                    ],
                    max_length=10
                )),
                ('specialite', models.CharField(
                    blank=True, max_length=100
                )),
                ('departement', models.CharField(
                    blank=True, max_length=100
                )),
                ('credits_total', models.IntegerField(default=60)),
                ('duree_semestres', models.IntegerField(default=2)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'formation',
                'ordering': ['niveau', 'libelle'],
            },
        ),

        # ── Table unite_enseignement ──────────────────────
        migrations.CreateModel(
            name='UniteEnseignement',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('formation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='unites',
                    to='dossier.formation'
                )),
                ('code_ue', models.CharField(max_length=20)),
                ('libelle_ue', models.CharField(max_length=150)),
                ('semestre', models.IntegerField()),
                ('credit', models.IntegerField(default=3)),
                ('coefficient', models.DecimalField(
                    decimal_places=1, default=1.0, max_digits=3
                )),
                ('type_ue', models.CharField(
                    choices=[
                        ('obligatoire','Obligatoire'),
                        ('optionnel','Optionnel'),
                        ('libre','Libre'),
                    ],
                    default='obligatoire', max_length=20
                )),
                ('volume_horaire', models.IntegerField(
                    blank=True, null=True
                )),
                ('actif', models.BooleanField(default=True)),
            ],
            options={
                'db_table'        : 'unite_enseignement',
                'ordering'        : ['semestre', 'code_ue'],
                'unique_together' : {('formation', 'code_ue')},
            },
        ),

        # ── Table dossier_etudiant ────────────────────────
        migrations.CreateModel(
            name='DossierEtudiant',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('etudiant_id', models.IntegerField(unique=True)),
                ('formation', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='dossier.formation'
                )),
                ('annee_universitaire', models.CharField(max_length=10)),
                ('etat_dossier', models.CharField(
                    choices=[
                        ('en_cours',  'En cours de constitution'),
                        ('incomplet', 'Incomplet'),
                        ('complet',   'Complet'),
                        ('valide',    'Validé'),
                        ('rejete',    'Rejeté'),
                    ],
                    default='en_cours', max_length=20
                )),
                ('score_completude', models.IntegerField(default=0)),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('date_validation', models.DateField(
                    blank=True, null=True
                )),
                ('observation', models.TextField(blank=True)),
                ('valide_par', models.IntegerField(
                    blank=True, null=True
                )),
            ],
            options={
                'db_table': 'dossier_etudiant',
                'ordering': ['-date_creation'],
            },
        ),

        # ── Table piece_justificative ─────────────────────
        migrations.CreateModel(
            name='PieceJustificative',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('dossier', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pieces',
                    to='dossier.dossieretudiant'
                )),
                ('type_piece', models.CharField(
                    choices=[
                        ('bac',                 'Baccalauréat'),
                        ('cni',                 "Carte Nationale d'Identité"),
                        ('photo',               "Photo d'identité"),
                        ('diplome',             'Diplôme'),
                        ('releve_notes',        'Relevé de notes'),
                        ('acte_naissance',      'Acte de naissance'),
                        ('certificat_medical',  'Certificat médical'),
                        ('quitus_bibliotheque', 'Quitus bibliothèque'),
                        ('recu_paiement',       'Reçu de paiement'),
                        ('autre',               'Autre document'),
                    ],
                    max_length=30
                )),
                ('nom_fichier', models.CharField(max_length=255)),
                ('chemin_stockage', models.CharField(max_length=500)),
                ('taille_fichier', models.IntegerField(
                    blank=True, null=True
                )),
                ('type_mime', models.CharField(blank=True, max_length=50)),
                ('statut_verification', models.CharField(
                    choices=[
                        ('en_attente', 'En attente de vérification'),
                        ('valide',     'Validée'),
                        ('rejete',     'Rejetée'),
                        ('expire',     'Expirée'),
                    ],
                    default='en_attente', max_length=20
                )),
                ('motif_rejet', models.TextField(blank=True)),
                ('est_obligatoire', models.BooleanField(default=True)),
                ('date_expiration', models.DateField(
                    blank=True, null=True
                )),
                ('date_depot', models.DateTimeField(auto_now_add=True)),
                ('date_verification', models.DateTimeField(
                    blank=True, null=True
                )),
                ('verifie_par', models.IntegerField(
                    blank=True, null=True
                )),
            ],
            options={
                'db_table': 'piece_justificative',
                'ordering': ['type_piece', '-date_depot'],
            },
        ),

        # ── Données initiales — formations UADB ──────────
        migrations.RunPython(
            code         = charger_formations_initiales,
            reverse_code = migrations.RunPython.noop,
        ),
    ]
