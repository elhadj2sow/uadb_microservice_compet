from django.contrib import admin
from .models import (Inscription, Paiement,
                     ValidationService, Workflow, EtapeWorkflow)


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'etudiant_id', 'formation_id',
        'annee_universitaire', 'statut_inscription',
        'numero_provisoire', 'numero_matricule',
        'date_preinscription'
    ]
    list_filter   = ['statut_inscription', 'annee_universitaire',
                     'type_inscription']
    search_fields = ['etudiant_id', 'numero_provisoire', 'numero_matricule']
    readonly_fields = ['date_preinscription', 'date_inscription']


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'inscription', 'montant', 'montant_paye',
        'mode_paiement', 'statut_paiement', 'date_paiement'
    ]
    list_filter   = ['statut_paiement', 'mode_paiement']
    search_fields = ['reference_paiement']


@admin.register(ValidationService)
class ValidationServiceAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'inscription_id', 'type_service',
        'statut_validation', 'date_validation', 'valide_par'
    ]
    list_filter   = ['type_service', 'statut_validation']
    search_fields = ['inscription_id']


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'inscription', 'statut',
        'etape_courante', 'date_creation', 'date_fin'
    ]
    list_filter   = ['statut']


@admin.register(EtapeWorkflow)
class EtapeWorkflowAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'workflow', 'nom_etape', 'ordre',
        'statut', 'date_debut', 'date_fin', 'relances_envoyees'
    ]
    list_filter   = ['statut', 'ordre']
