from django.urls import path
from .views import (
    # Délibérations
    DeliberationListView,
    DeliberationDetailView,
    DemarrerDeliberationView,
    CloturerDeliberationView,
    PVDeliberationView,
    StatistiquesDeliberationView,
    # Résultats
    ResultatListView,
    ResultatDetailView,
    MesResultatsView,
    # Notes
    SaisirNoteView,
    SaisirNotesBulkView,
    NotesEtudiantView,
)

urlpatterns = [

    # ── Délibérations ─────────────────────────────────────
    path(
        'deliberations/',
        DeliberationListView.as_view(),
        name='deliberations-list'
    ),
    path(
        'deliberations/statistiques/',
        StatistiquesDeliberationView.as_view(),
        name='deliberations-stats'
    ),
    path(
        'deliberations/<int:pk>/',
        DeliberationDetailView.as_view(),
        name='deliberation-detail'
    ),
    path(
        'deliberations/<int:pk>/cloturer/',
        CloturerDeliberationView.as_view(),
        name='deliberation-cloturer'
    ),
    path(
        'deliberations/<int:pk>/demarrer/',
        DemarrerDeliberationView.as_view(),
        name='deliberation-demarrer'
    ),
    path(
        'deliberations/<int:pk>/pv/',
        PVDeliberationView.as_view(),
        name='deliberation-pv'
    ),

    # ── Résultats ─────────────────────────────────────────
    path(
        'deliberations/<int:pk>/resultats/',
        ResultatListView.as_view(),
        name='resultats-list'
    ),
    path(
        'resultats/mes-resultats/',
        MesResultatsView.as_view(),
        name='mes-resultats'
    ),
    path(
        'resultats/<int:pk>/',
        ResultatDetailView.as_view(),
        name='resultat-detail'
    ),
    path(
        'resultats/<int:pk>/notes/',
        NotesEtudiantView.as_view(),
        name='notes-etudiant'
    ),

    # ── Notes ─────────────────────────────────────────────
    path(
        'resultats/<int:pk>/notes/saisir/',
        SaisirNoteView.as_view(),
        name='saisir-note'
    ),
    path(
        'deliberations/<int:pk>/notes/bulk/',
        SaisirNotesBulkView.as_view(),
        name='saisir-notes-bulk'
    ),
]
