from django.contrib import admin
from .models import JournalAudit, StatistiqueAudit


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'action', 'niveau', 'statut',
        'acteur', 'service', 'ressource',
        'etudiant_id', 'adresse_ip', 'date_action'
    ]
    list_filter   = [
        'action', 'niveau', 'statut', 'service'
    ]
    search_fields = [
        'acteur', 'ressource', 'description',
        'adresse_ip', 'etudiant_id'
    ]
    readonly_fields = [
        'date_action', 'utilisateur_id', 'acteur',
        'role_acteur', 'action', 'niveau', 'statut',
        'description', 'service', 'ressource',
        'ressource_id', 'ressource_type',
        'etudiant_id', 'inscription_id', 'dossier_id',
        'deliberation_id', 'attestation_id',
        'adresse_ip', 'user_agent', 'methode_http',
        'url', 'details', 'message_erreur'
    ]
    date_hierarchy = 'date_action'
    ordering       = ['-date_action']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Seul le superuser peut supprimer depuis l'admin
        return request.user.is_superuser


@admin.register(StatistiqueAudit)
class StatistiqueAuditAdmin(admin.ModelAdmin):
    list_display  = [
        'date', 'nb_actions', 'nb_connexions',
        'nb_echecs', 'nb_alertes', 'date_calcul'
    ]
    readonly_fields = [
        'date', 'nb_actions', 'nb_connexions',
        'nb_echecs', 'nb_alertes',
        'stats_services', 'stats_actions', 'date_calcul'
    ]
    ordering = ['-date']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
