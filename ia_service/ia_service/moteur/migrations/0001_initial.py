from django.db import migrations, models
import django.db.models.deletion


def _charger_regles_initiales_proxy(apps, schema_editor):
    # Delegate to function defined later in this migration module.
    return charger_regles_initiales(apps, schema_editor)


def _creer_moteur_proxy(apps, schema_editor):
    # Delegate to function defined later in this migration module.
    return creer_moteur(apps, schema_editor)


class Migration(migrations.Migration):

    initial      = True
    dependencies = []

    operations = [

        # ── Créer le schéma PostgreSQL ────────────────────
        migrations.RunSQL(
            sql         = "CREATE SCHEMA IF NOT EXISTS ia;",
            reverse_sql = "DROP SCHEMA IF EXISTS ia CASCADE;",
        ),

        # ── Table regle_metier ────────────────────────────
        migrations.CreateModel(
            name='RegleMetier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_regle',   models.CharField(max_length=60, unique=True)),
                ('libelle',      models.CharField(max_length=200)),
                ('description',  models.TextField(blank=True)),
                ('domaine',      models.CharField(choices=[('dossier','Dossier étudiant'),('inscription','Inscription administrative'),('deliberation','Délibération'),('attestation','Attestation'),('workflow','Workflow')], max_length=20)),
                ('condition',    models.TextField()),
                ('action',       models.CharField(max_length=50)),
                ('priorite',     models.IntegerField(default=10)),
                ('active',       models.BooleanField(default=True)),
                ('date_creation',models.DateTimeField(auto_now_add=True)),
                ('date_maj',     models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'regle_metier', 'ordering': ['priorite', 'domaine']},
        ),

        # ── Table moteur_decision ─────────────────────────
        migrations.CreateModel(
            name='MoteurDecision',
            fields=[
                ('id',      models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom',     models.CharField(default='Moteur UADB v1', max_length=100)),
                ('version', models.CharField(default='1.0.0', max_length=20)),
                ('statut',  models.CharField(choices=[('actif','Actif'),('inactif','Inactif')], default='actif', max_length=20)),
                ('regles',  models.ManyToManyField(blank=True, related_name='moteurs', to='moteur.reglemetier')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'moteur_decision'},
        ),

        # ── Table decision_automatique ────────────────────
        migrations.CreateModel(
            name='DecisionAutomatique',
            fields=[
                ('id',             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_decision',  models.CharField(choices=[('completude_dossier','Complétude dossier'),('eligibilite_inscription','Éligibilité inscription'),('validation_deliberation','Validation délibération'),('eligibilite_attestation','Éligibilité attestation'),('detection_anomalie','Détection anomalie')], max_length=30)),
                ('date_decision',  models.DateTimeField(auto_now_add=True)),
                ('resultat',       models.CharField(max_length=30)),
                ('motif',          models.TextField(blank=True)),
                ('niveau_confiance', models.FloatField(default=1.0)),
                ('regle_appliquee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='decisions', to='moteur.reglemetier')),
                ('etudiant_id',    models.IntegerField(blank=True, null=True)),
                ('dossier_id',     models.IntegerField(blank=True, null=True)),
                ('inscription_id', models.IntegerField(blank=True, null=True)),
                ('deliberation_id',models.IntegerField(blank=True, null=True)),
                ('demande_id',     models.IntegerField(blank=True, null=True)),
                ('contexte_json',  models.JSONField(blank=True, null=True)),
            ],
            options={'db_table': 'decision_automatique', 'ordering': ['-date_decision']},
        ),

        # ── Table alerte_anomalie ─────────────────────────
        migrations.CreateModel(
            name='AlerteAnomalie',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_alerte',      models.CharField(choices=[('dossier_incomplet','Dossier incomplet depuis trop longtemps'),('piece_expiree','Pièce justificative expirée'),('note_aberrante','Note aberrante détectée'),('doublon','Doublon détecté'),('delai_depasse','Délai de traitement dépassé'),('incoherence','Incohérence dans les données')], max_length=30)),
                ('date_detection',   models.DateTimeField(auto_now_add=True)),
                ('niveau_gravite',   models.CharField(choices=[('faible','Faible'),('moyenne','Moyenne'),('elevee','Élevée'),('critique','Critique')], default='moyenne', max_length=20)),
                ('description',      models.TextField()),
                ('statut_traitement',models.CharField(choices=[('ouverte','Ouverte'),('en_cours','En cours de traitement'),('resolue','Résolue'),('ignoree','Ignorée')], default='ouverte', max_length=20)),
                ('date_resolution',  models.DateTimeField(blank=True, null=True)),
                ('resolu_par',       models.IntegerField(blank=True, null=True)),
                ('note_resolution',  models.TextField(blank=True)),
                ('etudiant_id',      models.IntegerField(blank=True, null=True)),
                ('dossier_id',       models.IntegerField(blank=True, null=True)),
                ('inscription_id',   models.IntegerField(blank=True, null=True)),
                ('deliberation_id',  models.IntegerField(blank=True, null=True)),
            ],
            options={'db_table': 'alerte_anomalie', 'ordering': ['-date_detection']},
        ),

        # ── Données initiales — Règles métier UADB ────────
        migrations.RunPython(
            code         = _charger_regles_initiales_proxy,
            reverse_code = migrations.RunPython.noop,
        ),

        # ── Instance du moteur ─────────────────────────────
        migrations.RunPython(
            code         = _creer_moteur_proxy,
            reverse_code = migrations.RunPython.noop,
        ),
    ]


def charger_regles_initiales(apps, schema_editor):
    """
    Insère toutes les règles métier de l'UADB.
    Modifiables depuis l'admin Django sans redéploiement.
    """
    RegleMetier = apps.get_model('moteur', 'RegleMetier')

    regles = [
        # ── Domaine : dossier ────────────────────────────
        {
            'code_regle' : 'DOSSIER_COMPLET',
            'libelle'    : 'Dossier complet à 100%',
            'domaine'    : 'dossier',
            'condition'  : "contexte['score_completude'] == 100",
            'action'     : 'complet',
            'priorite'   : 1,
        },
        {
            'code_regle' : 'DOSSIER_EN_COURS',
            'libelle'    : 'Dossier en cours (≥ 50%)',
            'domaine'    : 'dossier',
            'condition'  : "contexte['score_completude'] >= 50 and contexte['score_completude'] < 100",
            'action'     : 'en_cours',
            'priorite'   : 2,
        },
        {
            'code_regle' : 'DOSSIER_INCOMPLET',
            'libelle'    : 'Dossier incomplet (< 50%)',
            'domaine'    : 'dossier',
            'condition'  : "contexte['score_completude'] < 50",
            'action'     : 'incomplet',
            'priorite'   : 3,
        },

        # ── Domaine : délibération ───────────────────────
        {
            'code_regle' : 'DELIB_ADMIS',
            'libelle'    : 'Admission définitive',
            'domaine'    : 'deliberation',
            'condition'  : "contexte['moyenne'] >= 10 and contexte['credits'] >= 60",
            'action'     : 'admis',
            'priorite'   : 1,
        },
        {
            'code_regle' : 'DELIB_RATTRAPAGE',
            'libelle'    : 'Admis au rattrapage',
            'domaine'    : 'deliberation',
            'condition'  : "contexte['moyenne'] >= 8 and contexte['moyenne'] < 10",
            'action'     : 'rattrapage',
            'priorite'   : 2,
        },
        {
            'code_regle' : 'DELIB_AJOURNE',
            'libelle'    : 'Ajourné',
            'domaine'    : 'deliberation',
            'condition'  : "contexte['moyenne'] < 8",
            'action'     : 'ajourné',
            'priorite'   : 3,
        },

        # ── Domaine : attestation ────────────────────────
        {
            'code_regle' : 'ATT_INSCRIPTION_OK',
            'libelle'    : 'Éligible — inscription validée',
            'domaine'    : 'attestation',
            'condition'  : "contexte['inscription_validee'] == True",
            'action'     : 'eligible',
            'priorite'   : 1,
        },
        {
            'code_regle' : 'ATT_REUSSITE_OK',
            'libelle'    : 'Éligible — attestation de réussite',
            'domaine'    : 'attestation',
            'condition'  : (
                "contexte['type_att'] in ('reussite','passage') "
                "and contexte['decision'] == 'admis'"
            ),
            'action'     : 'eligible',
            'priorite'   : 2,
        },
        {
            'code_regle' : 'ATT_NON_ELIGIBLE',
            'libelle'    : 'Non éligible — inscription non validée',
            'domaine'    : 'attestation',
            'condition'  : "contexte['inscription_validee'] == False",
            'action'     : 'non_eligible',
            'priorite'   : 10,
        },

        # ── Domaine : inscription ────────────────────────
        {
            'code_regle' : 'INSC_ELIGIBLE',
            'libelle'    : 'Éligible à l\'inscription — dossier complet et paiement confirmé',
            'domaine'    : 'inscription',
            'condition'  : (
                "contexte['score_dossier'] == 100 "
                "and contexte['paiement_confirme'] == True"
            ),
            'action'     : 'eligible',
            'priorite'   : 1,
        },
        {
            'code_regle' : 'INSC_DOSSIER_INCOMPLET',
            'libelle'    : 'Non éligible — dossier incomplet',
            'domaine'    : 'inscription',
            'condition'  : "contexte['score_dossier'] < 100",
            'action'     : 'dossier_incomplet',
            'priorite'   : 2,
        },
        {
            'code_regle' : 'INSC_PAIEMENT_MANQUANT',
            'libelle'    : 'Non éligible — paiement non confirmé',
            'domaine'    : 'inscription',
            'condition'  : "contexte['paiement_confirme'] == False",
            'action'     : 'paiement_manquant',
            'priorite'   : 3,
        },
    ]

    for r in regles:
        RegleMetier.objects.get_or_create(
            code_regle=r['code_regle'],
            defaults=r
        )


def creer_moteur(apps, schema_editor):
    """Crée l'instance singleton du moteur de décision."""
    MoteurDecision = apps.get_model('moteur', 'MoteurDecision')
    MoteurDecision.objects.get_or_create(
        nom    ='Moteur UADB v1',
        defaults={
            'version': '1.0.0',
            'statut' : 'actif',
        }
    )
