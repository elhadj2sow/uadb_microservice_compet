from django.urls import path
from .views import (
    # Étudiant
    SoumettreDemandeView,
    MesDemandesView,
    MaDemandeDetailView,
    # Téléchargement
    TelechargerAttestationView,
    RegenererAttestationView,
    # Vérification publique
    VerifierAttestationView,
    # Admin / Agents
    DemandeListAdminView,
    DemandeDetailAdminView,
    StatistiquesAttestationView,
)

urlpatterns = [

    # ── Étudiant ──────────────────────────────────────────
    path(
        'attestations/demandes/',
        SoumettreDemandeView.as_view(),
        name='soumettre-demande'
    ),
    path(
        'attestations/mes-demandes/',
        MesDemandesView.as_view(),
        name='mes-demandes'
    ),
    path(
        'attestations/demandes/<int:pk>/',
        MaDemandeDetailView.as_view(),
        name='ma-demande-detail'
    ),

    # ── Téléchargement ────────────────────────────────────
    path(
        'attestations/<int:pk>/telecharger/',
        TelechargerAttestationView.as_view(),
        name='telecharger-attestation'
    ),
    path(
        'attestations/demandes/<int:pk>/regenerer/',
        RegenererAttestationView.as_view(),
        name='regenerer-attestation'
    ),

    # ── Vérification publique (sans authentification) ─────
    path(
        'attestations/verifier/<str:code>/',
        VerifierAttestationView.as_view(),
        name='verifier-attestation'
    ),

    # ── Admin / Agents ────────────────────────────────────
    path(
        'attestations/admin/demandes/',
        DemandeListAdminView.as_view(),
        name='admin-demandes-list'
    ),
    path(
        'attestations/admin/demandes/<int:pk>/',
        DemandeDetailAdminView.as_view(),
        name='admin-demande-detail'
    ),
    path(
        'attestations/statistiques/',
        StatistiquesAttestationView.as_view(),
        name='statistiques-attestations'
    ),
]
