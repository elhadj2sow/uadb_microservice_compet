from django.urls import path
from .views import (
    EvaluerView,
    RegleMetierListView, RegleMetierDetailView, TesterRegleView,
    DecisionListView, DecisionDetailView,
    AlerteListView, AlerteDetailView, ResoudreAlerteView,
    MoteurStatutView,
    StatistiquesIAView,
)

urlpatterns = [

    # ── Endpoint principal (appelé par tous les services) ─
    path(
        'evaluer/',
        EvaluerView.as_view(),
        name='evaluer'
    ),

    # ── Règles métier ─────────────────────────────────────
    path(
        'regles/',
        RegleMetierListView.as_view(),
        name='regles-list'
    ),
    path(
        'regles/<int:pk>/',
        RegleMetierDetailView.as_view(),
        name='regle-detail'
    ),
    path(
        'regles/<int:pk>/tester/',
        TesterRegleView.as_view(),
        name='regle-tester'
    ),

    # ── Décisions automatiques ────────────────────────────
    path(
        'decisions/',
        DecisionListView.as_view(),
        name='decisions-list'
    ),
    path(
        'decisions/<int:pk>/',
        DecisionDetailView.as_view(),
        name='decision-detail'
    ),

    # ── Alertes anomalies ─────────────────────────────────
    path(
        'alertes/',
        AlerteListView.as_view(),
        name='alertes-list'
    ),
    path(
        'alertes/<int:pk>/',
        AlerteDetailView.as_view(),
        name='alerte-detail'
    ),
    path(
        'alertes/<int:pk>/resoudre/',
        ResoudreAlerteView.as_view(),
        name='alerte-resoudre'
    ),

    # ── Moteur et statistiques ────────────────────────────
    path(
        'moteur/statut/',
        MoteurStatutView.as_view(),
        name='moteur-statut'
    ),
    path(
        'statistiques/',
        StatistiquesIAView.as_view(),
        name='statistiques-ia'
    ),
]
