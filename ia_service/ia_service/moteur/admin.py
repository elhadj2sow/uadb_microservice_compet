from django.contrib import admin
from .models import RegleMetier, MoteurDecision, DecisionAutomatique, AlerteAnomalie


@admin.register(RegleMetier)
class RegleMetierAdmin(admin.ModelAdmin):
    list_display  = [
        'code_regle', 'libelle', 'domaine',
        'action', 'priorite', 'active', 'date_maj'
    ]
    list_filter   = ['domaine', 'active']
    search_fields = ['code_regle', 'libelle', 'condition']
    list_editable = ['active', 'priorite']
    readonly_fields = ['date_creation', 'date_maj']

    fieldsets = (
        ('Identification', {
            'fields': ('code_regle', 'libelle', 'description', 'domaine')
        }),
        ('Règle', {
            'fields': ('condition', 'action', 'priorite', 'active'),
            'description': (
                'La condition est une expression Python utilisant '
                'contexte[\'cle\']. Ex: contexte[\'score\'] == 100'
            )
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_maj'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MoteurDecision)
class MoteurDecisionAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'version', 'statut', 'date_creation']
    filter_horizontal = ['regles']


@admin.register(DecisionAutomatique)
class DecisionAutomatiqueAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'type_decision', 'resultat', 'niveau_confiance',
        'etudiant_id', 'date_decision'
    ]
    list_filter   = ['type_decision', 'resultat']
    search_fields = ['etudiant_id', 'resultat']
    readonly_fields = ['date_decision', 'contexte_json']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AlerteAnomalie)
class AlerteAnomalieAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'type_alerte', 'niveau_gravite',
        'etudiant_id', 'statut_traitement', 'date_detection'
    ]
    list_filter   = ['type_alerte', 'niveau_gravite', 'statut_traitement']
    search_fields = ['etudiant_id', 'description']
    readonly_fields = ['date_detection']
    list_editable = ['statut_traitement']

    actions = ['marquer_resolues', 'marquer_ignorees']

    @admin.action(description='Marquer comme résolues')
    def marquer_resolues(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            statut_traitement='resolue',
            date_resolution=timezone.now(),
            resolu_par=request.user.id
        )

    @admin.action(description='Marquer comme ignorées')
    def marquer_ignorees(self, request, queryset):
        queryset.update(statut_traitement='ignoree')
