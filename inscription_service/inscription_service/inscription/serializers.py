from rest_framework import serializers
from .models import (Inscription, Paiement,
                     ValidationService, Workflow, EtapeWorkflow)


class EtapeWorkflowSerializer(serializers.ModelSerializer):
    service = serializers.SerializerMethodField()

    class Meta:
        model  = EtapeWorkflow
        fields = [
            'id', 'nom_etape', 'ordre', 'statut',
            'service', 'date_debut', 'date_fin',
            'delai_max_heures', 'relances_envoyees'
        ]

    def get_service(self, obj):
        return obj.validation_service.type_service


class WorkflowSerializer(serializers.ModelSerializer):
    etapes = EtapeWorkflowSerializer(many=True, read_only=True)
    progression = serializers.SerializerMethodField()

    class Meta:
        model  = Workflow
        fields = [
            'id', 'nom_workflow', 'statut',
            'etape_courante', 'progression',
            'date_creation', 'date_fin', 'etapes'
        ]

    def get_progression(self, obj):
        total  = obj.etapes.count()
        valides = obj.etapes.filter(statut='validee').count()
        if total == 0:
            return 0
        return round((valides / total) * 100)


class ValidationServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ValidationService
        fields = [
            'id', 'type_service', 'statut_validation',
            'date_validation', 'observation', 'valide_par'
        ]


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Paiement
        fields = [
            'id', 'montant', 'montant_paye', 'mode_paiement',
            'reference_paiement', 'statut_paiement',
            'date_paiement', 'date_confirmation', 'recu_path'
        ]


class InscriptionSerializer(serializers.ModelSerializer):
    workflow    = WorkflowSerializer(read_only=True)
    paiement    = PaiementSerializer(read_only=True)
    validations = serializers.SerializerMethodField()

    class Meta:
        model  = Inscription
        fields = [
            'id', 'etudiant_id', 'formation_id', 'dossier_id',
            'annee_universitaire', 'type_inscription',
            'statut_inscription', 'numero_provisoire',
            'numero_matricule', 'date_preinscription',
            'date_inscription', 'observation',
            'workflow', 'paiement', 'validations'
        ]

    def get_validations(self, obj):
        qs = ValidationService.objects.filter(
            inscription_id=obj.id
        ).order_by('id')
        return ValidationServiceSerializer(qs, many=True).data


class InscriptionListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes (sans détails workflow)."""
    progression = serializers.SerializerMethodField()

    class Meta:
        model  = Inscription
        fields = [
            'id', 'etudiant_id', 'formation_id',
            'annee_universitaire', 'type_inscription',
            'statut_inscription', 'numero_provisoire',
            'numero_matricule', 'date_preinscription',
            'progression'
        ]

    def get_progression(self, obj):
        try:
            wf     = obj.workflow
            total  = wf.etapes.count()
            valides = wf.etapes.filter(statut='validee').count()
            if total == 0:
                return 0
            return round((valides / total) * 100)
        except Exception:
            return 0


class PreinscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour la soumission initiale par l'étudiant."""

    class Meta:
        model  = Inscription
        fields = ['formation_id', 'annee_universitaire', 'type_inscription']

    def validate_annee_universitaire(self, value):
        import re
        if not re.match(r'^\d{4}-\d{4}$', value):
            raise serializers.ValidationError(
                "Format invalide. Utilisez : 2024-2025"
            )
        return value

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            return data
        etudiant_id = getattr(request.user, 'etudiant_id', None)
        if not etudiant_id:
            raise serializers.ValidationError(
                "Profil étudiant introuvable dans le token."
            )
        existe = Inscription.objects.filter(
            etudiant_id         = etudiant_id,
            annee_universitaire = data['annee_universitaire']
        ).exists()
        if existe:
            raise serializers.ValidationError(
                "Vous êtes déjà inscrit pour cette année universitaire."
            )
        return data


class ValiderEtapeSerializer(serializers.Serializer):
    action      = serializers.ChoiceField(
        choices=['valider', 'rejeter'],
        default='valider'
    )
    observation = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )


class PaiementCreateSerializer(serializers.Serializer):
    montant             = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    montant_paye        = serializers.DecimalField(max_digits=10, decimal_places=2)
    mode_paiement       = serializers.ChoiceField(choices=[
        'especes', 'virement', 'orange_money', 'wave', 'cheque'
    ])
    reference_paiement  = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )


class PaiementSoumissionSerializer(serializers.Serializer):
    """Soumission de preuve de paiement par l'etudiant."""
    montant_paye = serializers.DecimalField(max_digits=10, decimal_places=2)
    mode_paiement = serializers.ChoiceField(choices=[
        'especes', 'virement', 'orange_money', 'wave', 'cheque'
    ])
    reference_paiement = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    recu_path = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )
