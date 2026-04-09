from django.urls import path
from .views import (
    # Notifications
    EnvoyerNotificationView,
    MesNotificationsView,
    MarquerLueView,
    MarquerToutesLuesView,
    NotificationListAdminView,
    RelancerEchecsView,
    StatistiquesNotificationView,
    # Chatbot
    DemarrerConversationView,
    EnvoyerMessageView,
    MesConversationsView,
    ConversationDetailView,
    # Base de connaissance
    BaseConnaissanceListView,
    BaseConnaissanceDetailView,
    TesterChatbotView,
)

urlpatterns = [

    # ── Envoi (appelé par les autres microservices) ───────
    path(
        'notifications/',
        EnvoyerNotificationView.as_view(),
        name='envoyer-notification'
    ),

    # ── Étudiant — consultation ───────────────────────────
    path(
        'notifications/mes-notifications/',
        MesNotificationsView.as_view(),
        name='mes-notifications'
    ),
    path(
        'notifications/tout-lire/',
        MarquerToutesLuesView.as_view(),
        name='tout-lire'
    ),
    path(
        'notifications/<int:pk>/lire/',
        MarquerLueView.as_view(),
        name='marquer-lue'
    ),

    # ── Admin / Agents ────────────────────────────────────
    path(
        'notifications/admin/',
        NotificationListAdminView.as_view(),
        name='notifications-admin'
    ),
    path(
        'notifications/admin/relancer/',
        RelancerEchecsView.as_view(),
        name='relancer-echecs'
    ),
    path(
        'notifications/statistiques/',
        StatistiquesNotificationView.as_view(),
        name='statistiques-notifications'
    ),

    # ── Chatbot — conversations ───────────────────────────
    path(
        'chatbot/conversations/',
        DemarrerConversationView.as_view(),
        name='demarrer-conversation'
    ),
    path(
        'chatbot/conversations/mes-conversations/',
        MesConversationsView.as_view(),
        name='mes-conversations'
    ),
    path(
        'chatbot/conversations/<int:pk>/',
        ConversationDetailView.as_view(),
        name='conversation-detail'
    ),
    path(
        'chatbot/conversations/<int:pk>/messages/',
        EnvoyerMessageView.as_view(),
        name='envoyer-message'
    ),

    # ── Base de connaissance ──────────────────────────────
    path(
        'chatbot/base-connaissance/',
        BaseConnaissanceListView.as_view(),
        name='base-connaissance-list'
    ),
    path(
        'chatbot/base-connaissance/<int:pk>/',
        BaseConnaissanceDetailView.as_view(),
        name='base-connaissance-detail'
    ),
    path(
        'chatbot/tester/',
        TesterChatbotView.as_view(),
        name='tester-chatbot'
    ),
]
