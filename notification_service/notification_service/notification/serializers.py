from rest_framework import serializers
from .models import Notification, Conversation, Message, BaseConnaissance


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = [
            'id', 'etudiant_id', 'service_destinataire',
            'type_notification', 'canal', 'sujet', 'message',
            'statut_envoi', 'date_notification', 'date_envoi',
            'date_lecture', 'erreur', 'emetteur_service',
            'nb_tentatives', 'inscription_id', 'dossier_id',
            'deliberation_id', 'attestation_id'
        ]
        read_only_fields = [
            'statut_envoi', 'date_notification',
            'date_envoi', 'erreur', 'nb_tentatives'
        ]


class EnvoyerNotificationSerializer(serializers.Serializer):
    """
    Serializer pour l'endpoint principal d'envoi.
    Appelé par tous les autres microservices.
    """
    etudiant_id          = serializers.IntegerField(
        required=False, allow_null=True
    )
    service_destinataire = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=''
    )
    canal                = serializers.ChoiceField(
        choices=['email', 'sms', 'interne', 'push'],
        default='email'
    )
    message              = serializers.CharField()
    type_notification    = serializers.ChoiceField(
        choices=[
            'inscription', 'dossier', 'deliberation',
            'attestation', 'workflow', 'paiement',
            'systeme', 'chatbot'
        ],
        default='systeme'
    )
    sujet                = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=''
    )
    emetteur_service     = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=''
    )
    # Références optionnelles
    inscription_id       = serializers.IntegerField(
        required=False, allow_null=True
    )
    dossier_id           = serializers.IntegerField(
        required=False, allow_null=True
    )
    deliberation_id      = serializers.IntegerField(
        required=False, allow_null=True
    )
    attestation_id       = serializers.IntegerField(
        required=False, allow_null=True
    )

    def validate(self, data):
        if not data.get('etudiant_id') and not data.get('service_destinataire'):
            raise serializers.ValidationError(
                "etudiant_id ou service_destinataire est requis."
            )
        return data


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = [
            'id', 'contenu', 'emetteur',
            'date_envoi', 'intention', 'confiance', 'lu'
        ]
        read_only_fields = [
            'emetteur', 'date_envoi', 'intention', 'confiance'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    messages    = MessageSerializer(many=True, read_only=True)
    nb_messages = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Conversation
        fields = [
            'id', 'etudiant_id', 'statut',
            'date_debut', 'date_fin',
            'nb_messages', 'messages'
        ]
        read_only_fields = [
            'etudiant_id', 'date_debut',
            'date_fin', 'nb_messages'
        ]


class ConversationListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Conversation
        fields = [
            'id', 'etudiant_id', 'statut',
            'date_debut', 'date_fin', 'nb_messages'
        ]


class EnvoyerMessageSerializer(serializers.Serializer):
    """Message envoyé par l'étudiant au chatbot."""
    contenu = serializers.CharField(max_length=1000)


class BaseConnaissanceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BaseConnaissance
        fields = [
            'id', 'titre', 'categorie', 'questions',
            'mots_cles', 'contenu', 'actif',
            'priorite', 'date_creation', 'date_maj'
        ]
