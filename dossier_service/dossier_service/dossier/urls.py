from django.urls import path
from .views import (
    # Formations
    FormationListView,
    FormationDetailView,
    FormationCreateView,
    UniteEnseignementListView,
    UECreateView,
    UEDetailView,
    # Dossiers
    CreerDossierView,
    MonDossierView,
    MesDossiersView,
    DossierListView,
    DossierDetailView,
    DossierIncompletListView,
    StatistiquesDossierView,
    # Pièces
    DeposerPieceView,
    PiecesListView,
    VerifierPieceView,
    TelechargerPieceView,
    SupprimerPieceView,
)

urlpatterns = [

    # ── Formations ────────────────────────────────────────
    path(
        'formations/',
        FormationListView.as_view(),
        name='formations-list'
    ),
    path(
        'formations/creer/',
        FormationCreateView.as_view(),
        name='formation-creer'
    ),
    path(
        'formations/<int:pk>/',
        FormationDetailView.as_view(),
        name='formation-detail'
    ),
    path(
        'formations/<int:pk>/modifier/',
        FormationCreateView.as_view(),
        name='formation-modifier'
    ),
    path(
        'formations/<int:pk>/ues/',
        UniteEnseignementListView.as_view(),
        name='formation-ues'
    ),
    path(
        'formations/<int:pk>/ues/creer/',
        UECreateView.as_view(),
        name='formation-ue-creer'
    ),
    path(
        'formations/<int:pk>/ues/<int:ue_pk>/modifier/',
        UEDetailView.as_view(),
        name='formation-ue-modifier'
    ),
    path(
        'formations/<int:pk>/ues/<int:ue_pk>/supprimer/',
        UEDetailView.as_view(),
        name='formation-ue-supprimer'
    ),

    # ── Dossiers — Étudiant ───────────────────────────────
    path(
        'dossiers/',
        CreerDossierView.as_view(),
        name='creer-dossier'
    ),
    path(
        'dossiers/mon-dossier/',
        MonDossierView.as_view(),
        name='mon-dossier'
    ),
    path(
        'dossiers/mes-dossiers/',
        MesDossiersView.as_view(),
        name='mes-dossiers'
    ),

    # ── Dossiers — Agents / Admin ─────────────────────────
    path(
        'dossiers/liste/',
        DossierListView.as_view(),
        name='dossiers-liste'
    ),
    path(
        'dossiers/statistiques/',
        StatistiquesDossierView.as_view(),
        name='dossiers-stats'
    ),
    path(
        'dossiers/incomplets/',
        DossierIncompletListView.as_view(),
        name='dossiers-incomplets'
    ),
    path(
        'dossiers/<int:pk>/',
        DossierDetailView.as_view(),
        name='dossier-detail'
    ),

    # ── Pièces justificatives ─────────────────────────────
    path(
        'dossiers/<int:pk>/pieces/',
        DeposerPieceView.as_view(),
        name='deposer-piece'
    ),
    path(
        'dossiers/<int:pk>/pieces/liste/',
        PiecesListView.as_view(),
        name='pieces-liste'
    ),
    path(
        'pieces/<int:pk>/verifier/',
        VerifierPieceView.as_view(),
        name='verifier-piece'
    ),
    path(
        'pieces/<int:pk>/telecharger/',
        TelechargerPieceView.as_view(),
        name='telecharger-piece'
    ),
    path(
        'pieces/<int:pk>/',
        SupprimerPieceView.as_view(),
        name='supprimer-piece'
    ),
]
