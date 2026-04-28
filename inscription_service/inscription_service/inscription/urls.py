from django.urls import path
from .views import (
    PreinscriptionView,
    AutoCreateInscriptionView,
    MonInscriptionView,
    MesInscriptionsView,
    InscriptionListView,
    InscriptionDetailView,
    ValiderEtapeView,
    StatutWorkflowView,
    PaiementView,
    PayTechInitPaiementView,
    PayTechWebhookView,
    PayTechConfirmerSuccessView,
    StatistiquesView,
    EtapesBloqueeView,
    ReinscriptionEligibiliteView,
    ReinscriptionView,
    SituationBibliothequeView,
    EmpruntLivreListView,
    EmpruntLivreDetailView,
    PenaliteListView,
    PenaliteDetailView,
)

urlpatterns = [

    # ── Étudiant ──────────────────────────────────────────
    path(
        'inscriptions/',
        PreinscriptionView.as_view(),
        name='preinscription'
    ),
    path(
        'inscriptions/auto-create/',
        AutoCreateInscriptionView.as_view(),
        name='auto-create-inscription'
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

    # ── Réinscription ─────────────────────────────────────
    path(
        'inscriptions/reinscription/eligibilite/',
        ReinscriptionEligibiliteView.as_view(),
        name='reinscription-eligibilite'
    ),
    path(
        'inscriptions/reinscription/',
        ReinscriptionView.as_view(),
        name='reinscription'
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
    path(
        'inscriptions/<int:pk>/paiement/paytech/initier/',
        PayTechInitPaiementView.as_view(),
        name='paiement-paytech-initier'
    ),
    path(
        'paiements/paytech/webhook/',
        PayTechWebhookView.as_view(),
        name='paiement-paytech-webhook'
    ),
    path(
        'paiements/confirmer-success/',
        PayTechConfirmerSuccessView.as_view(),
        name='paiement-confirmer-success'
    ),

    # ── Usage interne (service IA) ────────────────────────
    path(
        'workflows/etapes-bloquees/',
        EtapesBloqueeView.as_view(),
        name='etapes-bloquees'
    ),

    # ── Bibliothèque ──────────────────────────────────────
    path(
        'bibliotheque/situation/<int:etudiant_id>/',
        SituationBibliothequeView.as_view(),
        name='bibliotheque-situation'
    ),
    path(
        'bibliotheque/emprunts/',
        EmpruntLivreListView.as_view(),
        name='bibliotheque-emprunts'
    ),
    path(
        'bibliotheque/emprunts/<int:pk>/',
        EmpruntLivreDetailView.as_view(),
        name='bibliotheque-emprunt-detail'
    ),
    path(
        'bibliotheque/penalites/',
        PenaliteListView.as_view(),
        name='bibliotheque-penalites'
    ),
    path(
        'bibliotheque/penalites/<int:pk>/',
        PenaliteDetailView.as_view(),
        name='bibliotheque-penalite-detail'
    ),
]
