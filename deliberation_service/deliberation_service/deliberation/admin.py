from django.contrib import admin
from .models import Deliberation, Resultat, Note


class NoteInline(admin.TabularInline):
    model         = Note
    extra         = 0
    readonly_fields = ['valeur', 'est_validee', 'date_saisie', 'date_modification']
    fields        = [
        'code_ue', 'libelle_ue', 'semestre', 'credit_ue',
        'note_cc', 'note_tp', 'note_examen', 'valeur',
        'est_validee', 'note_rattrapage', 'verrouille'
    ]


class ResultatInline(admin.TabularInline):
    model         = Resultat
    extra         = 0
    readonly_fields = ['moyenne_annuelle', 'credits_valides', 'date_creation']
    fields        = [
        'etudiant_id', 'moyenne_annuelle', 'credits_valides',
        'credits_total', 'decision', 'mention', 'rang'
    ]


@admin.register(Deliberation)
class DeliberationAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'session', 'annee_universitaire', 'semestre',
        'niveau', 'formation_id', 'statut', 'date_deliberation',
        'date_creation'
    ]
    list_filter   = ['statut', 'session', 'annee_universitaire', 'niveau']
    search_fields = ['annee_universitaire', 'formation_id']
    readonly_fields = ['date_creation', 'date_cloture']
    inlines       = [ResultatInline]


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'etudiant_id', 'deliberation',
        'moyenne_annuelle', 'credits_valides',
        'decision', 'mention', 'rang', 'date_creation'
    ]
    list_filter   = ['decision', 'mention']
    search_fields = ['etudiant_id']
    readonly_fields = [
        'moyenne_annuelle', 'credits_valides',
        'date_creation', 'date_validation'
    ]
    inlines       = [NoteInline]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'resultat', 'code_ue', 'libelle_ue',
        'note_cc', 'note_tp', 'note_examen', 'valeur',
        'est_validee', 'verrouille', 'date_saisie'
    ]
    list_filter   = ['est_validee', 'verrouille', 'semestre']
    search_fields = ['code_ue', 'libelle_ue']
    readonly_fields = ['valeur', 'est_validee', 'date_saisie', 'date_modification']

    def has_delete_permission(self, request, obj=None):
        if obj and obj.verrouille:
            return False
        return super().has_delete_permission(request, obj)
