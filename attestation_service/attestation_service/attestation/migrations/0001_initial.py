import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial      = True
    dependencies = []

    operations = [

        # ── Créer le schéma PostgreSQL ────────────────────
        migrations.RunSQL(
            sql         = "CREATE SCHEMA IF NOT EXISTS attestation;",
            reverse_sql = "DROP SCHEMA IF EXISTS attestation CASCADE;",
        ),

        # ── Table demande_attestation ─────────────────────
        migrations.CreateModel(
            name='DemandeAttestation',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('etudiant_id', models.IntegerField()),
                ('type_attestation', models.CharField(
                    choices=[
                        ('inscription',  "Attestation d'inscription"),
                        ('passage',      'Attestation de passage'),
                        ('reussite',     'Attestation de réussite'),
                        ('releve_notes', 'Relevé de notes'),
                        ('scolarite',    'Certificat de scolarité'),
                    ],
                    max_length=20
                )),
                ('annee_universitaire', models.CharField(
                    blank=True, max_length=10
                )),
                ('motif', models.TextField(blank=True)),
                ('statut', models.CharField(
                    choices=[
                        ('en_attente', 'En attente'),
                        ('approuvee',  'Approuvée'),
                        ('refusee',    'Refusée'),
                        ('generee',    'Générée'),
                    ],
                    default='en_attente', max_length=20
                )),
                ('decision_ia', models.CharField(
                    blank=True, max_length=20
                )),
                ('motif_refus', models.TextField(blank=True)),
                ('inscription_id', models.IntegerField(
                    blank=True, null=True
                )),
                ('deliberation_id', models.IntegerField(
                    blank=True, null=True
                )),
                ('date_demande', models.DateTimeField(auto_now_add=True)),
                ('date_traitement', models.DateTimeField(
                    blank=True, null=True
                )),
                ('traite_par', models.IntegerField(
                    blank=True, null=True
                )),
            ],
            options={
                'db_table': 'demande_attestation',
                'ordering': ['-date_demande'],
            },
        ),

        # ── Table attestation ─────────────────────────────
        migrations.CreateModel(
            name='Attestation',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('demande', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attestation',
                    to='attestation.demandeAttestation'
                )),
                ('type_attestation', models.CharField(max_length=20)),
                ('annee_universitaire', models.CharField(
                    blank=True, max_length=10
                )),
                ('numero_ordre', models.CharField(
                    max_length=30, unique=True
                )),
                ('code_verification', models.CharField(
                    default=uuid.uuid4,
                    max_length=64,
                    unique=True
                )),
                ('pdf_path', models.CharField(
                    blank=True, max_length=500
                )),
                ('qr_code_path', models.CharField(
                    blank=True, max_length=500
                )),
                ('statut_attestation', models.CharField(
                    choices=[
                        ('generee',  'Générée'),
                        ('delivree', 'Délivrée'),
                        ('annulee',  'Annulée'),
                    ],
                    default='generee', max_length=20
                )),
                ('signature_electronique', models.BooleanField(
                    default=True
                )),
                ('signe_par', models.IntegerField(
                    blank=True, null=True
                )),
                ('date_generation', models.DateTimeField(
                    auto_now_add=True
                )),
                ('date_retrait', models.DateTimeField(
                    blank=True, null=True
                )),
            ],
            options={
                'db_table': 'attestation',
                'ordering': ['-date_generation'],
            },
        ),
    ]
