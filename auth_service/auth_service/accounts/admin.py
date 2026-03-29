from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Etudiant, Role, JournalAudit


class EtudiantInline(admin.StackedInline):
    model  = Etudiant
    extra  = 0
    fields = [
        'nom', 'prenom', 'matricule', 'ine',
        'date_naissance', 'sexe', 'telephone', 'statut'
    ]


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    inlines     = [EtudiantInline]
    list_display = [
        'username', 'email', 'etat_compte',
        'get_roles', 'date_joined', 'is_active'
    ]
    list_filter  = ['etat_compte', 'roles', 'is_active']
    search_fields = ['username', 'email']

    fieldsets = UserAdmin.fieldsets + (
        ('UADB', {'fields': ('roles', 'etat_compte')}),
    )

    @admin.display(description='Rôles')
    def get_roles(self, obj):
        return ', '.join(obj.role_list) or '—'


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'nom', 'prenom', 'matricule',
        'ine', 'telephone', 'statut'
    ]
    list_filter   = ['statut', 'sexe']
    search_fields = ['nom', 'prenom', 'matricule', 'ine']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'libelle']


@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display  = [
        'id', 'action', 'acteur',
        'ressource', 'adresse_ip', 'date_action'
    ]
    list_filter   = ['action']
    search_fields = ['acteur', 'ressource']
    readonly_fields = [
        'utilisateur', 'date_action', 'action',
        'ressource', 'acteur', 'adresse_ip',
        'user_agent', 'details'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
