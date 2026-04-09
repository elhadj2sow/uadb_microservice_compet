from django.contrib import admin
from .models import Notification, Conversation, Message, BaseConnaissance


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'type_notification', 'canal', 'etudiant_id',
        'service_destinataire', 'statut_envoi',
        'emetteur_service', 'date_notification', 'nb_tentatives'
    ]
    list_filter   = ['statut_envoi', 'canal', 'type_notification']
    search_fields = ['etudiant_id', 'message', 'emetteur_service']
    readonly_fields = [
        'date_notification', 'date_envoi',
        'date_lecture', 'nb_tentatives'
    ]
    actions = ['relancer_echecs']

    @admin.action(description='Relancer les notifications en échec')
    def relancer_echecs(self, request, queryset):
        from .services import NotificationService
        service = NotificationService()
        nb = service.retenter_echecs()
        self.message_user(request, f'{nb} notification(s) renvoyée(s).')


class MessageInline(admin.TabularInline):
    model         = Message
    extra         = 0
    readonly_fields = ['date_envoi', 'intention', 'confiance']
    fields        = ['emetteur', 'contenu', 'intention',
                     'confiance', 'date_envoi', 'lu']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'etudiant_id', 'statut',
        'nb_messages', 'date_debut', 'date_fin'
    ]
    list_filter   = ['statut']
    search_fields = ['etudiant_id']
    readonly_fields = ['date_debut', 'nb_messages']
    inlines       = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'conversation', 'emetteur',
        'contenu_court', 'intention', 'confiance', 'date_envoi'
    ]
    list_filter   = ['emetteur']
    readonly_fields = ['date_envoi']

    @admin.display(description='Contenu')
    def contenu_court(self, obj):
        return obj.contenu[:60] + '...' if len(obj.contenu) > 60 else obj.contenu


@admin.register(BaseConnaissance)
class BaseConnaissanceAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'titre', 'categorie', 'actif', 'priorite', 'date_maj'
    ]
    list_filter   = ['categorie', 'actif']
    search_fields = ['titre', 'questions', 'mots_cles', 'contenu']
    list_editable = ['actif', 'priorite']
