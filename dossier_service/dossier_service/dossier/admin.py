from django.contrib import admin
from .models import (Formation, UniteEnseignement,
                     DossierEtudiant, PieceJustificative)


class UniteEnseignementInline(admin.TabularInline):
    model  = UniteEnseignement
    extra  = 0
    fields = ['code_ue', 'libelle_ue', 'semestre',
              'credit', 'coefficient', 'type_ue', 'actif']


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display  = [
        'code_formation', 'libelle', 'niveau',
        'specialite', 'credits_total', 'actif'
    ]
    list_filter   = ['niveau', 'actif']
    search_fields = ['code_formation', 'libelle']
    inlines       = [UniteEnseignementInline]


@admin.register(UniteEnseignement)
class UniteEnseignementAdmin(admin.ModelAdmin):
    list_display  = [
        'code_ue', 'libelle_ue', 'formation',
        'semestre', 'credit', 'type_ue', 'actif'
    ]
    list_filter   = ['semestre', 'type_ue', 'actif', 'formation']
    search_fields = ['code_ue', 'libelle_ue']


class PieceJustificativeInline(admin.TabularInline):
    model         = PieceJustificative
    extra         = 0
    readonly_fields = ['date_depot', 'date_verification']
    fields        = [
        'type_piece', 'nom_fichier', 'statut_verification',
        'est_obligatoire', 'date_depot', 'date_expiration'
    ]


@admin.register(DossierEtudiant)
class DossierEtudiantAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'etudiant_id', 'formation',
        'annee_universitaire', 'etat_dossier',
        'score_completude', 'date_creation'
    ]
    list_filter   = ['etat_dossier', 'annee_universitaire', 'formation']
    search_fields = ['etudiant_id']
    readonly_fields = ['date_creation', 'score_completude']
    inlines       = [PieceJustificativeInline]


@admin.register(PieceJustificative)
class PieceJustificativeAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'dossier', 'type_piece', 'nom_fichier',
        'statut_verification', 'est_obligatoire', 'date_depot'
    ]
    list_filter   = ['type_piece', 'statut_verification', 'est_obligatoire']
    search_fields = ['nom_fichier', 'dossier__etudiant_id']
    readonly_fields = ['date_depot', 'date_verification', 'chemin_stockage']

    def has_add_permission(self, request):
        return False
