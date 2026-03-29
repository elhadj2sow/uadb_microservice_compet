from django.urls import path
from .views import (
    PreinscriptionView,
    MonInscriptionView,
    MesInscriptionsView,
    InscriptionListView,
    InscriptionDetailView,
    ValiderEtapeView,
    StatutWorkflowView,
    PaiementView,
    StatistiquesView,
    EtapesBloqueeView,
)

urlpatterns = [

    # ── Étudiant ──────────────────────────────────────────
    path(
        'inscriptions/',
        PreinscriptionView.as_view(),
        name='preinscription'
    ),
    path(
        'inscriptions/mon-inscription/',
        MonInscriptionView.as_view(),
        name='mon-inscription'
    ),
    path(
        'inscriptions/mes-inscriptions/',
        MesInscriptionsView.as_view(),
        name='mes-inscriptions'
    ),

    # ── Agents / Administration ───────────────────────────
    path(
        'inscriptions/liste/',
        InscriptionListView.as_view(),
        name='liste-inscriptions'
    ),
    path(
        'inscriptions/statistiques/',
        StatistiquesView.as_view(),
        name='statistiques'
    ),
    path(
        'inscriptions/<int:pk>/',
        InscriptionDetailView.as_view(),
        name='detail-inscription'
    ),
    path(
        'inscriptions/<int:pk>/valider-etape/',
        ValiderEtapeView.as_view(),
        name='valider-etape'
    ),
    path(
        'inscriptions/<int:pk>/workflow/',
        StatutWorkflowView.as_view(),
        name='statut-workflow'
    ),

    # ── Paiement ─────────────────────────────────────────
    path(
        'inscriptions/<int:pk>/paiement/',
        PaiementView.as_view(),
        name='paiement'
    ),

    # ── Usage interne (service IA) ────────────────────────
    path(
        'workflows/etapes-bloquees/',
        EtapesBloqueeView.as_view(),
        name='etapes-bloquees'
    ),
]
