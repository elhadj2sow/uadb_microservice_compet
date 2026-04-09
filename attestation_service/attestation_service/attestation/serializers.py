from rest_framework import serializers
from .models import DemandeAttestation, Attestation


class AttestationSerializer(serializers.ModelSerializer):
    url_telechargement = serializers.SerializerMethodField()

    class Meta:
        model  = Attestation
        fields = [
            'id', 'type_attestation', 'annee_universitaire',
            'numero_ordre', 'code_verification',
            'statut_attestation', 'signature_electronique',
            'date_generation', 'date_retrait',
            'url_telechargement'
        ]

    def get_url_telechargement(self, obj):
        from .storage import generer_url_telechargement
        if obj.pdf_path:
            return generer_url_telechargement(obj.pdf_path)
        return None


class DemandeAttestationSerializer(serializers.ModelSerializer):
    attestation         = AttestationSerializer(read_only=True)
    type_label          = serializers.SerializerMethodField()

    class Meta:
        model  = DemandeAttestation
        fields = [
            'id', 'etudiant_id', 'type_attestation', 'type_label',
            'annee_universitaire', 'motif', 'statut',
            'decision_ia', 'motif_refus',
            'inscription_id', 'deliberation_id',
            'date_demande', 'date_traitement', 'traite_par',
            'attestation'
        ]
        read_only_fields = [
            'statut', 'decision_ia', 'motif_refus',
            'date_demande', 'date_traitement',
            'traite_par', 'attestation'
        ]

    def get_type_label(self, obj):
        return obj.get_type_attestation_display()


class SoumettreDemandeSerializer(serializers.Serializer):
    """Soumission d'une nouvelle demande par l'étudiant."""
    type_attestation    = serializers.ChoiceField(
        choices=DemandeAttestation.TYPE_CHOICES
    )
    annee_universitaire = serializers.CharField(
        max_length=10,
        required=False,
        allow_blank=True,
        default=''
    )
    motif               = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )

    def validate_annee_universitaire(self, value):
        import re
        if value and not re.match(r'^\d{4}-\d{4}$', value):
            raise serializers.ValidationError(
                "Format invalide. Utilisez : 2024-2025"
            )
        return value


class VerifierCodeSerializer(serializers.Serializer):
    """Vérification publique d'une attestation par son code."""
    code = serializers.CharField(max_length=64)


class DemandeListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes agents."""
    type_label = serializers.SerializerMethodField()

    class Meta:
        model  = DemandeAttestation
        fields = [
            'id', 'etudiant_id', 'type_attestation', 'type_label',
            'annee_universitaire', 'statut', 'date_demande'
        ]

    def get_type_label(self, obj):
        return obj.get_type_attestation_display()
