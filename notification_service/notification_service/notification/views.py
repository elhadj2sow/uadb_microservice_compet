from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from .models import Notification, Conversation, Message, BaseConnaissance
from .serializers import (
    NotificationSerializer, EnvoyerNotificationSerializer,
    ConversationSerializer, ConversationListSerializer,
    MessageSerializer, EnvoyerMessageSerializer,
    BaseConnaissanceSerializer,
)
from .permissions import EstEtudiant, EstAgentOuAdmin, EstAdmin
from .services import NotificationService
from .chatbot import MoteurChatbot
from .utils import tracer_action

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  NOTIFICATIONS — ENVOI (appelé par les autres services)
# ─────────────────────────────────────────────

class EnvoyerNotificationView(APIView):
    """
    POST /api/notifications/
    Point d'entrée unique appelé par tous les autres microservices
    pour envoyer une notification à un étudiant ou un service.

    Exemples d'appels depuis les autres services :
    - Service inscription : notifier l'étudiant après validation
    - Service dossier : notifier quand le dossier est complet
    - Service délibération : notifier les résultats
    - Service attestation : notifier la disponibilité du PDF
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EnvoyerNotificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data    = serializer.validated_data
        service = NotificationService()

        notif = service.envoyer(
            etudiant_id          = data.get('etudiant_id'),
            service_destinataire = data.get('service_destinataire', ''),
            canal                = data.get('canal', 'email'),
            message              = data['message'],
            type_notification    = data.get('type_notification', 'systeme'),
            sujet                = data.get('sujet', ''),
            emetteur_service     = data.get('emetteur_service', ''),
            inscription_id       = data.get('inscription_id'),
            dossier_id           = data.get('dossier_id'),
            deliberation_id      = data.get('deliberation_id'),
            attestation_id       = data.get('attestation_id'),
        )

        tracer_action(request, 'CREATE', f'notification/{notif.id}', details={
            'canal'           : data.get('canal', 'email'),
            'type_notification': data.get('type_notification', 'systeme'),
            'etudiant_id'     : data.get('etudiant_id'),
            'emetteur_service': data.get('emetteur_service', ''),
        })

        return Response(
            {
                'message'     : 'Notification traitée.',
                'id'          : notif.id,
                'statut_envoi': notif.statut_envoi,
            },
            status=status.HTTP_201_CREATED
        )


# ─────────────────────────────────────────────
#  NOTIFICATIONS — CONSULTATION ÉTUDIANT
# ─────────────────────────────────────────────

class MesNotificationsView(APIView):
    """
    GET /api/notifications/mes-notifications/
    L'étudiant consulte toutes ses notifications.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        qs = Notification.objects.filter(
            etudiant_id=request.user.etudiant_id
        ).order_by('-date_notification')

        # Filtres
        canal  = request.query_params.get('canal')
        statut = request.query_params.get('statut')
        type_n = request.query_params.get('type')
        non_lu = request.query_params.get('non_lu')

        if canal:
            qs = qs.filter(canal=canal)
        if statut:
            qs = qs.filter(statut_envoi=statut)
        if type_n:
            qs = qs.filter(type_notification=type_n)
        if non_lu == 'true':
            qs = qs.filter(statut_envoi='envoye', date_lecture__isnull=True)

        return Response({
            'count'  : qs.count(),
            'non_lues': qs.filter(
                statut_envoi='envoye',
                date_lecture__isnull=True
            ).count(),
            'results': NotificationSerializer(qs, many=True).data,
        })


class MarquerLueView(APIView):
    """
    PATCH /api/notifications/{id}/lire/
    Marque une notification comme lue.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def patch(self, request, pk):
        notif = get_object_or_404(
            Notification,
            pk          = pk,
            etudiant_id = request.user.etudiant_id
        )
        if not notif.date_lecture:
            notif.statut_envoi = 'lu'
            notif.date_lecture = timezone.now()
            notif.save()
        return Response({'message': 'Notification marquée comme lue.'})


class MarquerToutesLuesView(APIView):
    """
    POST /api/notifications/tout-lire/
    Marque toutes les notifications de l'étudiant comme lues.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def post(self, request):
        nb = Notification.objects.filter(
            etudiant_id   = request.user.etudiant_id,
            statut_envoi  = 'envoye',
            date_lecture__isnull = True
        ).update(
            statut_envoi = 'lu',
            date_lecture = timezone.now()
        )
        return Response({
            'message'    : f'{nb} notification(s) marquée(s) comme lues.',
            'nb_marquees': nb,
        })


# ─────────────────────────────────────────────
#  NOTIFICATIONS — GESTION ADMIN
# ─────────────────────────────────────────────

class NotificationListAdminView(APIView):
    """
    GET /api/notifications/admin/
    Admin : lister toutes les notifications avec filtres.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        qs = Notification.objects.all().order_by('-date_notification')

        # Filtres
        statut     = request.query_params.get('statut')
        canal      = request.query_params.get('canal')
        type_n     = request.query_params.get('type')
        etudiant   = request.query_params.get('etudiant_id')
        service    = request.query_params.get('service')

        if statut:
            qs = qs.filter(statut_envoi=statut)
        if canal:
            qs = qs.filter(canal=canal)
        if type_n:
            qs = qs.filter(type_notification=type_n)
        if etudiant:
            qs = qs.filter(etudiant_id=etudiant)
        if service:
            qs = qs.filter(emetteur_service=service)

        return Response({
            'count'  : qs.count(),
            'echecs' : qs.filter(statut_envoi='echec').count(),
            'results': NotificationSerializer(qs[:100], many=True).data,
        })


class RelancerEchecsView(APIView):
    """
    POST /api/notifications/admin/relancer/
    Retente l'envoi des notifications en échec.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def post(self, request):
        service    = NotificationService()
        nb_reussis = service.retenter_echecs()
        return Response({
            'message'   : f'{nb_reussis} notification(s) renvoyée(s).',
            'nb_reussis': nb_reussis,
        })


class StatistiquesNotificationView(APIView):
    """
    GET /api/notifications/statistiques/
    Tableau de bord des notifications.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        qs = Notification.objects.all()

        from django.db.models import Count
        stats = {
            'total'        : qs.count(),
            'par_statut'   : {},
            'par_canal'    : {},
            'par_type'     : {},
            'taux_reussite': 0,
        }

        for s in ('en_attente', 'envoye', 'echec', 'lu'):
            stats['par_statut'][s] = qs.filter(statut_envoi=s).count()

        for c in ('email', 'sms', 'interne', 'push'):
            stats['par_canal'][c] = qs.filter(canal=c).count()

        for t, _ in Notification.TYPE_CHOICES:
            stats['par_type'][t] = qs.filter(type_notification=t).count()

        total = qs.count()
        if total:
            envoyes = qs.filter(
                statut_envoi__in=('envoye', 'lu')
            ).count()
            stats['taux_reussite'] = round((envoyes / total) * 100, 1)

        return Response(stats)


# ─────────────────────────────────────────────
#  CHATBOT — CONVERSATIONS
# ─────────────────────────────────────────────

class DemarrerConversationView(APIView):
    """
    POST /api/chatbot/conversations/
    L'étudiant démarre une nouvelle conversation avec le chatbot.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def post(self, request):
        # Terminer les conversations actives précédentes
        Conversation.objects.filter(
            etudiant_id = request.user.etudiant_id,
            statut      = 'active'
        ).update(statut='terminee', date_fin=timezone.now())

        conversation = Conversation.objects.create(
            etudiant_id = request.user.etudiant_id,
            statut      = 'active',
            contexte    = request.data.get('contexte', {}),
        )

        # Message de bienvenue automatique
        msg_bienvenue = (
            "Bonjour ! Je suis l'assistant virtuel de l'UADB. "
            "Je suis disponible 24h/24 pour répondre à vos questions "
            "sur les inscriptions, dossiers, résultats et attestations. "
            "Comment puis-je vous aider ?"
        )
        Message.objects.create(
            conversation = conversation,
            contenu      = msg_bienvenue,
            emetteur     = 'chatbot',
            intention    = 'salutation',
            confiance    = 1.0,
        )
        conversation.nb_messages = 1
        conversation.save()

        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED
        )


class EnvoyerMessageView(APIView):
    """
    POST /api/chatbot/conversations/{id}/messages/
    L'étudiant envoie un message au chatbot.
    Le chatbot répond automatiquement.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def post(self, request, pk):
        conversation = get_object_or_404(
            Conversation,
            pk          = pk,
            etudiant_id = request.user.etudiant_id,
            statut      = 'active'
        )

        serializer = EnvoyerMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        contenu_etudiant = serializer.validated_data['contenu']

        # Enregistrer le message de l'étudiant
        msg_etudiant = Message.objects.create(
            conversation = conversation,
            contenu      = contenu_etudiant,
            emetteur     = 'etudiant',
        )

        # Générer la réponse du chatbot
        moteur  = MoteurChatbot()
        resultat = moteur.traiter_message(
            contenu_etudiant,
            contexte=conversation.contexte
        )

        # Enregistrer la réponse du chatbot
        msg_chatbot = Message.objects.create(
            conversation = conversation,
            contenu      = resultat['reponse'],
            emetteur     = 'chatbot',
            intention    = resultat.get('intention', ''),
            confiance    = resultat.get('confiance', 0.0),
        )

        # Mettre à jour le compteur
        conversation.nb_messages += 2
        conversation.save()

        return Response({
            'message_etudiant': MessageSerializer(msg_etudiant).data,
            'reponse_chatbot' : MessageSerializer(msg_chatbot).data,
            'intention'       : resultat.get('intention'),
            'confiance'       : resultat.get('confiance'),
            'source'          : resultat.get('source'),
        }, status=status.HTTP_201_CREATED)


class MesConversationsView(APIView):
    """
    GET /api/chatbot/conversations/
    Historique des conversations de l'étudiant.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        conversations = Conversation.objects.filter(
            etudiant_id=request.user.etudiant_id
        ).order_by('-date_debut')
        return Response(
            ConversationListSerializer(conversations, many=True).data
        )


class ConversationDetailView(APIView):
    """
    GET    /api/chatbot/conversations/{id}/  → historique messages
    DELETE /api/chatbot/conversations/{id}/  → terminer la conversation
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request, pk):
        conversation = get_object_or_404(
            Conversation,
            pk          = pk,
            etudiant_id = request.user.etudiant_id
        )
        return Response(ConversationSerializer(conversation).data)

    def delete(self, request, pk):
        conversation = get_object_or_404(
            Conversation,
            pk          = pk,
            etudiant_id = request.user.etudiant_id
        )
        conversation.statut   = 'terminee'
        conversation.date_fin = timezone.now()
        conversation.save()
        return Response({'message': 'Conversation terminée.'})


# ─────────────────────────────────────────────
#  BASE DE CONNAISSANCE (ADMIN)
# ─────────────────────────────────────────────

class BaseConnaissanceListView(APIView):
    """
    GET  /api/chatbot/base-connaissance/  → lister
    POST /api/chatbot/base-connaissance/  → créer (admin)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roles = getattr(request.user, 'roles', [])

        qs = BaseConnaissance.objects.all().order_by('priorite')
        if 'admin' not in roles:
            qs = qs.filter(actif=True)

        categorie = request.query_params.get('categorie')
        if categorie:
            qs = qs.filter(categorie=categorie)

        return Response({
            'count'  : qs.count(),
            'results': BaseConnaissanceSerializer(qs, many=True).data,
        })

    def post(self, request):
        roles = getattr(request.user, 'roles', [])
        if 'admin' not in roles:
            return Response(
                {'error': 'Réservé aux administrateurs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = BaseConnaissanceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        entree = serializer.save()
        return Response(
            BaseConnaissanceSerializer(entree).data,
            status=status.HTTP_201_CREATED
        )


class BaseConnaissanceDetailView(APIView):
    """
    GET    /api/chatbot/base-connaissance/{id}/  → détail
    PATCH  /api/chatbot/base-connaissance/{id}/  → modifier (admin)
    DELETE /api/chatbot/base-connaissance/{id}/  → supprimer (admin)
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request, pk):
        entree = get_object_or_404(BaseConnaissance, pk=pk)
        return Response(BaseConnaissanceSerializer(entree).data)

    def patch(self, request, pk):
        entree     = get_object_or_404(BaseConnaissance, pk=pk)
        serializer = BaseConnaissanceSerializer(
            entree, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        entree = get_object_or_404(BaseConnaissance, pk=pk)
        entree.delete()
        return Response(
            {'message': 'Entrée supprimée.'},
            status=status.HTTP_204_NO_CONTENT
        )


class TesterChatbotView(APIView):
    """
    POST /api/chatbot/tester/
    Teste le chatbot sans créer de conversation.
    Utile pour l'administrateur qui veut vérifier les réponses.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def post(self, request):
        texte   = request.data.get('message', '')
        moteur  = MoteurChatbot()
        resultat = moteur.traiter_message(texte)
        return Response({
            'message'  : texte,
            'reponse'  : resultat['reponse'],
            'intention': resultat['intention'],
            'confiance': resultat['confiance'],
            'source'   : resultat['source'],
        })
