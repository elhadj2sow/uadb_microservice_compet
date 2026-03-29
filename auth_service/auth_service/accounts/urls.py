from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    LogoutView,
    RegisterEtudiantView,
    MeView,
    ChangePasswordView,
    UtilisateurListView,
    UtilisateurDetailView,
    AssignerRoleView,
    MettreAJourMatriculeView,
    RoleListView,
    JournalAuditView,
)

urlpatterns = [

    # ── Authentification ──────────────────────────────────
    path('login/',
         LoginView.as_view(),
         name='login'),

    path('logout/',
         LogoutView.as_view(),
         name='logout'),

    path('refresh/',
         TokenRefreshView.as_view(),
         name='token_refresh'),

    path('register/',
         RegisterEtudiantView.as_view(),
         name='register'),

    # ── Profil utilisateur connecté ───────────────────────
    path('me/',
         MeView.as_view(),
         name='me'),

    path('change-password/',
         ChangePasswordView.as_view(),
         name='change-password'),

    # ── Gestion utilisateurs (admin) ──────────────────────
    path('utilisateurs/',
         UtilisateurListView.as_view(),
         name='utilisateurs-list'),

    path('utilisateurs/<int:pk>/',
         UtilisateurDetailView.as_view(),
         name='utilisateur-detail'),

    path('utilisateurs/<int:pk>/roles/',
         AssignerRoleView.as_view(),
         name='assigner-role'),

    # ── Endpoint interne (service inscription) ────────────
    path('etudiants/<int:pk>/matricule/',
         MettreAJourMatriculeView.as_view(),
         name='maj-matricule'),

    # ── Rôles ─────────────────────────────────────────────
    path('roles/',
         RoleListView.as_view(),
         name='roles-list'),

    # ── Journal d'audit ───────────────────────────────────
    path('audit/',
         JournalAuditView.as_view(),
         name='journal-audit'),
]
