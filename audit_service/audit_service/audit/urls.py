from django.urls import path
from .views import (
    TracerActionView,
    JournalListView,
    JournalDetailView,
    JournalEtudiantView,
    JournalUtilisateurView,
    StatistiquesView,
    StatistiquesDailyView,
    CalculerStatistiquesView,
    PurgerJournalView,
    ResumeActionsChoicesView,
)

urlpatterns = [

    # ── Traçage (appelé par tous les microservices) ───────
    path(
        'audit/tracer/',
        TracerActionView.as_view(),
        name='tracer-action'
    ),

    # ── Consultation du journal ───────────────────────────
    path(
        'audit/journal/',
        JournalListView.as_view(),
        name='journal-list'
    ),
    path(
        'audit/journal/<int:pk>/',
        JournalDetailView.as_view(),
        name='journal-detail'
    ),
    path(
        'audit/etudiants/<int:etudiant_id>/journal/',
        JournalEtudiantView.as_view(),
        name='journal-etudiant'
    ),
    path(
        'audit/utilisateurs/<int:utilisateur_id>/journal/',
        JournalUtilisateurView.as_view(),
        name='journal-utilisateur'
    ),

    # ── Statistiques ──────────────────────────────────────
    path(
        'audit/statistiques/',
        StatistiquesView.as_view(),
        name='statistiques'
    ),
    path(
        'audit/statistiques/daily/',
        StatistiquesDailyView.as_view(),
        name='statistiques-daily'
    ),
    path(
        'audit/statistiques/calculer/',
        CalculerStatistiquesView.as_view(),
        name='calculer-statistiques'
    ),

    # ── Maintenance ───────────────────────────────────────
    path(
        'audit/purger/',
        PurgerJournalView.as_view(),
        name='purger-journal'
    ),

    # ── Métadonnées (pour React) ──────────────────────────
    path(
        'audit/meta/',
        ResumeActionsChoicesView.as_view(),
        name='audit-meta'
    ),
]
