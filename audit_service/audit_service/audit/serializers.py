from rest_framework import serializers
from .models import JournalAudit, StatistiqueAudit


class JournalAuditSerializer(serializers.ModelSerializer):
    action_label  = serializers.SerializerMethodField()
    niveau_label  = serializers.SerializerMethodField()
    statut_label  = serializers.SerializerMethodField()

    class Meta:
        model  = JournalAudit
        fields = [
            'id', 'utilisateur_id', 'acteur', 'role_acteur',
            'action', 'action_label', 'niveau', 'niveau_label',
            'statut', 'statut_label', 'description',
            'service', 'ressource', 'ressource_id', 'ressource_type',
            'etudiant_id', 'inscription_id', 'dossier_id',
            'deliberation_id', 'attestation_id',
            'adresse_ip', 'methode_http', 'url',
            'details', 'message_erreur', 'date_action'
        ]
        read_only_fields = ['date_action']

    def get_action_label(self, obj):
        return obj.get_action_display()

    def get_niveau_label(self, obj):
        return obj.get_niveau_display()

    def get_statut_label(self, obj):
        return obj.get_statut_display()


class TracerActionSerializer(serializers.Serializer):
    """
    Serializer pour l'endpoint POST /api/audit/tracer/
    Appelé par tous les autres microservices.
    """
    # Acteur
    utilisateur_id  = serializers.IntegerField(
        required=False, allow_null=True
    )
    acteur          = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=''
    )
    role_acteur     = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=''
    )
    # Action
    action          = serializers.ChoiceField(
        choices=[c[0] for c in JournalAudit.ACTION_CHOICES]
    )
    niveau          = serializers.ChoiceField(
        choices=[c[0] for c in JournalAudit.NIVEAU_CHOICES],
        default='INFO'
    )
    statut          = serializers.ChoiceField(
        choices=[c[0] for c in JournalAudit.STATUT_CHOICES],
        default='succes'
    )
    description     = serializers.CharField(
        required=False, allow_blank=True, default=''
    )
    # Ressource
    service         = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=''
    )
    ressource       = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=''
    )
    ressource_id    = serializers.IntegerField(
        required=False, allow_null=True
    )
    ressource_type  = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=''
    )
    # Références inter-services
    etudiant_id     = serializers.IntegerField(
        required=False, allow_null=True
    )
    inscription_id  = serializers.IntegerField(
        required=False, allow_null=True
    )
    dossier_id      = serializers.IntegerField(
        required=False, allow_null=True
    )
    deliberation_id = serializers.IntegerField(
        required=False, allow_null=True
    )
    attestation_id  = serializers.IntegerField(
        required=False, allow_null=True
    )
    # Contexte technique
    adresse_ip      = serializers.CharField(
        max_length=45, required=False, allow_blank=True, default=''
    )
    url             = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=''
    )
    methode_http    = serializers.CharField(
        max_length=10, required=False, allow_blank=True, default=''
    )
    details         = serializers.JSONField(
        required=False, allow_null=True
    )
    message_erreur  = serializers.CharField(
        required=False, allow_blank=True, default=''
    )


class StatistiqueAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StatistiqueAudit
        fields = [
            'date', 'nb_actions', 'nb_connexions',
            'nb_echecs', 'nb_alertes',
            'stats_services', 'stats_actions', 'date_calcul'
        ]


class FiltreAuditSerializer(serializers.Serializer):
    """Serializer pour valider les filtres de recherche."""
    action         = serializers.CharField(required=False, allow_blank=True)
    service        = serializers.CharField(required=False, allow_blank=True)
    niveau         = serializers.CharField(required=False, allow_blank=True)
    statut         = serializers.CharField(required=False, allow_blank=True)
    utilisateur_id = serializers.IntegerField(required=False, allow_null=True)
    etudiant_id    = serializers.IntegerField(required=False, allow_null=True)
    date_debut     = serializers.DateField(required=False, allow_null=True)
    date_fin       = serializers.DateField(required=False, allow_null=True)
    recherche      = serializers.CharField(required=False, allow_blank=True)
    limit          = serializers.IntegerField(
        required=False, default=50, min_value=1, max_value=500
    )
    offset         = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
