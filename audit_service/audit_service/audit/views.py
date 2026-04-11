from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q
import logging

from .models import JournalAudit, StatistiqueAudit
from .serializers import (
    JournalAuditSerializer,
    TracerActionSerializer,
    StatistiqueAuditSerializer,
    FiltreAuditSerializer,
)
from .permissions import EstAdmin, EstAgentOuAdmin
from .utils import tracer, calculer_statistiques_jour

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  ENDPOINT PRINCIPAL — TRAÇAGE
# ─────────────────────────────────────────────

class TracerActionView(APIView):
    """
    POST /api/audit/tracer/
    Point d'entrée unique appelé par tous les microservices
    pour enregistrer une action dans le journal d'audit.

    Exemples d'utilisation :
    - Service auth : LOGIN, LOGOUT, CREATE utilisateur
    - Service inscription : VALIDATE, REJECT, WORKFLOW_START
    - Service dossier : UPLOAD pièce, VERIFY pièce
    - Service délibération : SAISIR note, CLOTURER
    - Service attestation : GENERATE, DOWNLOAD
    - Service IA : DECISION_AUTO, ALERTE
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TracerActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # IP réelle depuis la requête si non fournie
        adresse_ip = data.get('adresse_ip') or self._get_ip(request)

        try:
            entree = JournalAudit.objects.create(
                utilisateur_id  = data.get('utilisateur_id'),
                acteur          = data.get('acteur', ''),
                role_acteur     = data.get('role_acteur', ''),
                action          = data['action'],
                niveau          = data.get('niveau', 'INFO'),
                statut          = data.get('statut', 'succes'),
                description     = data.get('description', ''),
                service         = data.get('service', ''),
                ressource       = data.get('ressource', ''),
                ressource_id    = data.get('ressource_id'),
                ressource_type  = data.get('ressource_type', ''),
                etudiant_id     = data.get('etudiant_id'),
                inscription_id  = data.get('inscription_id'),
                dossier_id      = data.get('dossier_id'),
                deliberation_id = data.get('deliberation_id'),
                attestation_id  = data.get('attestation_id'),
                adresse_ip      = adresse_ip,
                url             = data.get('url', ''),
                methode_http    = data.get('methode_http', ''),
                details         = data.get('details'),
                message_erreur  = data.get('message_erreur', ''),
            )
            return Response(
                {
                    'message'   : 'Action tracée avec succès.',
                    'id'        : entree.id,
                    'date_action': entree.date_action,
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Erreur traçage audit : {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_ip(self, request):
        x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_fwd:
            return x_fwd.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


# ─────────────────────────────────────────────
#  CONSULTATION DU JOURNAL
# ─────────────────────────────────────────────

class JournalListView(APIView):
    """
    GET /api/audit/journal/
    Consulter le journal d'audit avec filtres avancés.
    Réservé aux agents et administrateurs.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        qs = JournalAudit.objects.all()

        # ── Filtres ───────────────────────────────────────
        action         = request.query_params.get('action')
        service        = request.query_params.get('service')
        niveau         = request.query_params.get('niveau')
        statut         = request.query_params.get('statut')
        utilisateur_id = request.query_params.get('utilisateur_id')
        etudiant_id    = request.query_params.get('etudiant_id')
        date_debut     = request.query_params.get('date_debut')
        date_fin       = request.query_params.get('date_fin')
        recherche      = request.query_params.get('recherche')
        ressource_type = request.query_params.get('ressource_type')
        limit          = int(request.query_params.get('limit',  50))
        offset         = int(request.query_params.get('offset',  0))

        # Limiter la taille max
        limit = min(limit, 500)

        if action:
            qs = qs.filter(action=action)
        if service:
            qs = qs.filter(service=service)
        if niveau:
            qs = qs.filter(niveau=niveau)
        if statut:
            qs = qs.filter(statut=statut)
        if utilisateur_id:
            qs = qs.filter(utilisateur_id=utilisateur_id)
        if etudiant_id:
            qs = qs.filter(etudiant_id=etudiant_id)
        if date_debut:
            qs = qs.filter(date_action__date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_action__date__lte=date_fin)
        if ressource_type:
            qs = qs.filter(ressource_type=ressource_type)
        if recherche:
            qs = qs.filter(
                Q(acteur__icontains=recherche)
                | Q(description__icontains=recherche)
                | Q(ressource__icontains=recherche)
            )

        total = qs.count()
        page  = qs[offset:offset + limit]

        return Response({
            'count'  : total,
            'limit'  : limit,
            'offset' : offset,
            'results': JournalAuditSerializer(page, many=True).data,
        })


class JournalDetailView(APIView):
    """GET /api/audit/journal/{id}/"""
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request, pk):
        entree = get_object_or_404(JournalAudit, pk=pk)
        return Response(JournalAuditSerializer(entree).data)


class JournalEtudiantView(APIView):
    """
    GET /api/audit/etudiants/{etudiant_id}/journal/
    Toutes les actions concernant un étudiant précis.
    Utile pour l'historique complet d'un étudiant.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request, etudiant_id):
        qs = JournalAudit.objects.filter(
            etudiant_id=etudiant_id
        ).order_by('-date_action')

        # Filtres optionnels
        action  = request.query_params.get('action')
        service = request.query_params.get('service')
        if action:
            qs = qs.filter(action=action)
        if service:
            qs = qs.filter(service=service)

        limit  = min(int(request.query_params.get('limit', 100)), 500)
        offset = int(request.query_params.get('offset', 0))

        return Response({
            'etudiant_id': etudiant_id,
            'count'      : qs.count(),
            'results'    : JournalAuditSerializer(
                qs[offset:offset + limit], many=True
            ).data,
        })


class JournalUtilisateurView(APIView):
    """
    GET /api/audit/utilisateurs/{utilisateur_id}/journal/
    Toutes les actions effectuées par un utilisateur précis.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request, utilisateur_id):
        qs = JournalAudit.objects.filter(
            utilisateur_id=utilisateur_id
        ).order_by('-date_action')

        limit  = min(int(request.query_params.get('limit', 100)), 500)
        offset = int(request.query_params.get('offset', 0))

        return Response({
            'utilisateur_id': utilisateur_id,
            'count'         : qs.count(),
            'results'       : JournalAuditSerializer(
                qs[offset:offset + limit], many=True
            ).data,
        })


# ─────────────────────────────────────────────
#  STATISTIQUES ET TABLEAU DE BORD
# ─────────────────────────────────────────────

class StatistiquesView(APIView):
    """
    GET /api/audit/statistiques/
    Tableau de bord complet du journal d'audit.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        # Période
        date_debut = request.query_params.get('date_debut')
        date_fin   = request.query_params.get('date_fin')

        qs = JournalAudit.objects.all()
        if date_debut:
            qs = qs.filter(date_action__date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_action__date__lte=date_fin)

        # Statistiques générales
        stats = {
            'periode'   : {
                'debut': date_debut or 'toutes dates',
                'fin'  : date_fin   or 'toutes dates',
            },
            'total'          : qs.count(),
            'par_niveau'     : {},
            'par_statut'     : {},
            'par_service'    : {},
            'par_action'     : {},
            'connexions'     : {
                'total'  : qs.filter(action='LOGIN').count(),
                'echecs' : qs.filter(action='LOGIN_ECHEC').count(),
            },
            'top_acteurs'    : [],
            'top_ressources' : [],
        }

        for niveau, _ in JournalAudit.NIVEAU_CHOICES:
            stats['par_niveau'][niveau] = qs.filter(niveau=niveau).count()

        for s, _ in JournalAudit.STATUT_CHOICES:
            stats['par_statut'][s] = qs.filter(statut=s).count()

        # Par service
        for item in qs.values('service').annotate(
            nb=Count('id')
        ).order_by('-nb')[:10]:
            stats['par_service'][item['service'] or 'inconnu'] = item['nb']

        # Par action (top 10)
        for item in qs.values('action').annotate(
            nb=Count('id')
        ).order_by('-nb')[:10]:
            stats['par_action'][item['action']] = item['nb']

        # Top acteurs
        stats['top_acteurs'] = list(
            qs.exclude(acteur='').values('acteur').annotate(
                nb=Count('id')
            ).order_by('-nb')[:5]
        )

        return Response(stats)


class StatistiquesDailyView(APIView):
    """
    GET /api/audit/statistiques/daily/
    Statistiques pré-calculées par jour (7 derniers jours).
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        nb_jours = int(request.query_params.get('jours', 7))
        nb_jours = min(nb_jours, 90)

        from datetime import date, timedelta
        today = date.today()
        dates = [today - timedelta(days=i) for i in range(nb_jours)]

        resultats = []
        for d in dates:
            # Recalculer si pas encore calculé
            try:
                stat = StatistiqueAudit.objects.get(date=d)
            except StatistiqueAudit.DoesNotExist:
                stat = calculer_statistiques_jour(d)
            resultats.append(StatistiqueAuditSerializer(stat).data)

        return Response({
            'nb_jours': nb_jours,
            'results' : resultats,
        })


class CalculerStatistiquesView(APIView):
    """
    POST /api/audit/statistiques/calculer/
    Recalcule les statistiques pour une date.
    Utile pour la maintenance ou si les stats sont obsolètes.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def post(self, request):
        date_str = request.data.get('date')
        if date_str:
            from datetime import date as date_type
            try:
                d = date_type.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {'error': 'Format date invalide. Utilisez YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            d = timezone.now().date()

        stat = calculer_statistiques_jour(d)
        return Response({
            'message': f'Statistiques calculées pour le {d}.',
            'stat'   : StatistiqueAuditSerializer(stat).data,
        })


# ─────────────────────────────────────────────
#  PURGE ET MAINTENANCE
# ─────────────────────────────────────────────

class PurgerJournalView(APIView):
    """
    DELETE /api/audit/purger/
    Supprime les entrées plus anciennes que N jours.
    Réservé aux administrateurs. Action irréversible.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def delete(self, request):
        from django.conf import settings
        retention = int(
            request.data.get(
                'retention_jours',
                getattr(settings, 'RETENTION_JOURS', 365)
            )
        )

        if retention <= 0:
            return Response(
                {'error': 'retention_jours doit être supérieur à 0.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        date_limite = timezone.now() - timezone.timedelta(days=retention)
        nb, _       = JournalAudit.objects.filter(
            date_action__lt=date_limite
        ).delete()

        # Tracer la purge elle-même
        tracer(
            action          = 'DELETE',
            service         = 'audit',
            utilisateur_id  = request.user.id,
            acteur          = request.user.username,
            description     = (
                f"Purge du journal d'audit : {nb} entrées supprimées "
                f"(antérieures au {date_limite.strftime('%d/%m/%Y')})."
            ),
            niveau          = 'WARNING',
            details         = {
                'nb_supprimes'  : nb,
                'retention_jours': retention,
                'date_limite'   : str(date_limite.date()),
            }
        )

        return Response({
            'message'       : f'{nb} entrée(s) supprimée(s).',
            'nb_supprimes'  : nb,
            'date_limite'   : date_limite.date(),
            'retention_jours': retention,
        })


class ResumeActionsChoicesView(APIView):
    """
    GET /api/audit/meta/
    Retourne les choix disponibles pour les filtres.
    Utile pour le frontend React.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'actions' : [
                {'value': c[0], 'label': c[1]}
                for c in JournalAudit.ACTION_CHOICES
            ],
            'niveaux' : [
                {'value': c[0], 'label': c[1]}
                for c in JournalAudit.NIVEAU_CHOICES
            ],
            'statuts' : [
                {'value': c[0], 'label': c[1]}
                for c in JournalAudit.STATUT_CHOICES
            ],
            'services': [
                'auth', 'inscription', 'dossier',
                'deliberation', 'attestation',
                'notification', 'ia', 'audit'
            ],
        })
