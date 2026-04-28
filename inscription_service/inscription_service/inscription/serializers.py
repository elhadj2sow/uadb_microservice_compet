from rest_framework import serializers
import json
from .models import (Inscription, Paiement,
                     ValidationService, Workflow, EtapeWorkflow,
                     EmpruntLivre, PenaliteBibliotheque)


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
            'date_paiement', 'date_confirmation', 'recu_path',
            'provider', 'transaction_id', 'transaction_token',
            'payment_url', 'statut_externe', 'date_callback'
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
    progression      = serializers.SerializerMethodField()
    etudiant_nom     = serializers.CharField(default='', read_only=True)
    formation_libelle = serializers.CharField(default='', read_only=True)

    class Meta:
        model  = Inscription
        fields = [
            'id', 'etudiant_id', 'etudiant_nom',
            'formation_id', 'formation_libelle',
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

        # Empêche une nouvelle inscription "premiere" si un historique existe déjà.
        type_inscription = data.get('type_inscription', 'premiere')
        if type_inscription == 'premiere':
            historique = Inscription.objects.filter(etudiant_id=etudiant_id)
            if historique.exists():
                raise serializers.ValidationError(
                    "Type d'inscription invalide: utilisez 'reinscription' "
                    "si vous avez déjà une inscription antérieure."
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


class PayTechInitSerializer(serializers.Serializer):
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    target_payment = serializers.CharField(required=False, allow_blank=True)


class PayTechWebhookSerializer(serializers.Serializer):
    ref_command = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True)
    item_ref = serializers.CharField(required=False, allow_blank=True)
    custom_field = serializers.CharField(required=False, allow_blank=True)
    token = serializers.CharField(required=False, allow_blank=True)
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    status = serializers.CharField(required=False, allow_blank=True)
    payment_status = serializers.CharField(required=False, allow_blank=True)
    type_event = serializers.CharField(required=False, allow_blank=True)
    event = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        custom_field = data.get('custom_field') or ''
        custom_reference = ''
        if custom_field:
            try:
                custom_data = json.loads(custom_field)
                if isinstance(custom_data, dict):
                    custom_reference = (
                        custom_data.get('reference')
                        or custom_data.get('ref_command')
                        or custom_data.get('item_ref')
                        or ''
                    )
            except Exception:
                custom_reference = ''

        reference = (
            data.get('ref_command')
            or data.get('reference')
            or data.get('item_ref')
            or custom_reference
            or data.get('custom_field')
        )
        if not reference:
            raise serializers.ValidationError(
                "Référence de commande PayTech introuvable dans le callback."
            )
        data['reference_resolue'] = reference

        status_resolu = (
            data.get('status')
            or data.get('payment_status')
            or data.get('type_event')
            or data.get('event')
            or ''
        )
        data['status_resolu'] = status_resolu
        return data


# ── Bibliothèque ──────────────────────────────────────────────────────────────

class PenaliteBibliothequeSerializer(serializers.ModelSerializer):
    motif_display  = serializers.CharField(source='get_motif_display',  read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model  = PenaliteBibliotheque
        fields = [
            'id', 'etudiant_id', 'emprunt',
            'motif', 'motif_display',
            'montant', 'statut', 'statut_display',
            'date_creation', 'date_paiement', 'observation',
            'enregistre_par',
        ]
        read_only_fields = ['date_creation', 'enregistre_par']


class EmpruntLivreSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    est_en_retard  = serializers.BooleanField(read_only=True)
    penalites      = PenaliteBibliothequeSerializer(many=True, read_only=True)

    class Meta:
        model  = EmpruntLivre
        fields = [
            'id', 'etudiant_id', 'numero_inventaire', 'titre_livre',
            'date_emprunt', 'date_retour_prevue', 'date_retour_effective',
            'statut', 'statut_display', 'est_en_retard', 'note',
            'enregistre_par', 'date_creation', 'penalites',
        ]
        read_only_fields = ['date_creation', 'enregistre_par']


class SituationBibliothequeSerializer(serializers.Serializer):
    """Résumé de la situation bibliothèque d'un étudiant."""
    etudiant_id          = serializers.IntegerField()
    livres_non_rendus    = EmpruntLivreSerializer(many=True)
    penalites_en_attente = PenaliteBibliothequeSerializer(many=True)
    peut_valider         = serializers.BooleanField()
    motif_blocage        = serializers.CharField(allow_blank=True)
