from rest_framework import serializers
from .models import RegleMetier, MoteurDecision, DecisionAutomatique, AlerteAnomalie


class RegleMetierSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RegleMetier
        fields = [
            'id', 'code_regle', 'libelle', 'description',
            'domaine', 'condition', 'action', 'priorite',
            'active', 'date_creation', 'date_maj'
        ]


class RegleMetierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RegleMetier
        fields = [
            'code_regle', 'libelle', 'description',
            'domaine', 'condition', 'action', 'priorite', 'active'
        ]

    def validate_condition(self, value):
        """Valide que la condition est une expression Python sûre."""
        contexte_test = {
            'score': 100, 'score_completude': 100,
            'moyenne': 12.5, 'credits': 60,
            'inscription_validee': True,
            'type_att': 'inscription', 'decision': 'admis',
            'paiement_confirme': True, 'score_dossier': 100,
        }
        try:
            from .engine import NAMESPACE_SECURISE
            ns = {**NAMESPACE_SECURISE, 'contexte': contexte_test}
            eval(value, ns)
        except Exception as e:
            raise serializers.ValidationError(
                f"Condition invalide : {e}. "
                f"Utilisez contexte['cle'] dans votre expression."
            )
        return value


class DecisionAutomatiqueSerializer(serializers.ModelSerializer):
    regle_code = serializers.SerializerMethodField()

    class Meta:
        model  = DecisionAutomatique
        fields = [
            'id', 'type_decision', 'date_decision',
            'resultat', 'motif', 'niveau_confiance',
            'regle_code', 'etudiant_id', 'dossier_id',
            'inscription_id', 'deliberation_id', 'demande_id',
            'contexte_json'
        ]

    def get_regle_code(self, obj):
        return obj.regle_appliquee.code_regle if obj.regle_appliquee else None


class AlerteAnomalieSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AlerteAnomalie
        fields = [
            'id', 'type_alerte', 'date_detection',
            'niveau_gravite', 'description', 'statut_traitement',
            'date_resolution', 'resolu_par', 'note_resolution',
            'etudiant_id', 'dossier_id',
            'inscription_id', 'deliberation_id'
        ]
        read_only_fields = ['date_detection']


class ResoudreAlerteSerializer(serializers.Serializer):
    statut_traitement = serializers.ChoiceField(
        choices=['resolue', 'ignoree', 'en_cours']
    )
    note_resolution   = serializers.CharField(
        required=False, allow_blank=True, default=''
    )


class EvaluerSerializer(serializers.Serializer):
    """
    Serializer pour le point d'entrée unique POST /api/evaluer/.
    Appelé par tous les autres microservices.
    """
    type = serializers.ChoiceField(choices=[
        'completude_dossier',
        'validation_deliberation',
        'eligibilite_attestation',
        'eligibilite_inscription',
    ])
    # Champs optionnels selon le type
    etudiant        = serializers.IntegerField(required=False, allow_null=True)
    dossier_id      = serializers.IntegerField(required=False, allow_null=True)
    inscription_id  = serializers.IntegerField(required=False, allow_null=True)
    deliberation_id = serializers.IntegerField(required=False, allow_null=True)
    demande_id      = serializers.IntegerField(required=False, allow_null=True)
    # Données spécifiques
    score           = serializers.IntegerField(required=False, allow_null=True)
    score_completude= serializers.IntegerField(required=False, allow_null=True)
    score_dossier   = serializers.IntegerField(required=False, allow_null=True)
    moyenne         = serializers.FloatField(required=False,   allow_null=True)
    credits         = serializers.IntegerField(required=False, allow_null=True)
    type_att        = serializers.CharField(required=False, allow_blank=True, default='')
    inscription_validee = serializers.BooleanField(required=False, default=False)
    decision        = serializers.CharField(required=False, allow_blank=True, default='')
    paiement_confirme   = serializers.BooleanField(required=False, default=False)


class MoteurDecisionSerializer(serializers.ModelSerializer):
    nb_regles = serializers.SerializerMethodField()

    class Meta:
        model  = MoteurDecision
        fields = ['id', 'nom', 'version', 'statut', 'nb_regles', 'date_creation']

    def get_nb_regles(self, obj):
        return obj.regles.filter(active=True).count()
