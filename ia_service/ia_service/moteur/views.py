from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from .models import RegleMetier, MoteurDecision, DecisionAutomatique, AlerteAnomalie
from .serializers import (
    RegleMetierSerializer, RegleMetierCreateSerializer,
    DecisionAutomatiqueSerializer,
    AlerteAnomalieSerializer, ResoudreAlerteSerializer,
    EvaluerSerializer, MoteurDecisionSerializer,
)
from .permissions import EstAdmin, EstAgentOuAdmin
from .services import dispatcher
from .utils import tracer_action

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  ENDPOINT PRINCIPAL — ÉVALUATION
# ─────────────────────────────────────────────

class EvaluerView(APIView):
    """
    POST /api/evaluer/
    Point d'entrée unique appelé par tous les autres microservices.
    Dispatch vers le bon service métier selon le champ 'type'.

    Types supportés :
    - completude_dossier
    - validation_deliberation
    - eligibilite_attestation
    - eligibilite_inscription
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EvaluerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        type_eval = serializer.validated_data['type']
        data      = serializer.validated_data

        logger.info(
            f"Évaluation demandée : type={type_eval} "
            f"— étudiant={data.get('etudiant')}"
        )

        resultat = dispatcher(type_eval, data)

        if 'error' in resultat:
            return Response(
                resultat,
                status=status.HTTP_400_BAD_REQUEST
            )

        tracer_action(request, 'DECISION_AUTO', f'ia/evaluer/{type_eval}', details={
            'type_eval'  : type_eval,
            'etudiant'   : data.get('etudiant'),
            'decision'   : resultat.get('decision') or resultat.get('eligible'),
        })

        return Response(resultat, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
#  RÈGLES MÉTIER
# ─────────────────────────────────────────────

class RegleMetierListView(APIView):
    """
    GET  /api/regles/  → lister les règles
    POST /api/regles/  → créer une règle (admin)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = RegleMetier.objects.all()

        # Filtres
        domaine = request.query_params.get('domaine')
        active  = request.query_params.get('active')
        if domaine:
            qs = qs.filter(domaine=domaine)
        if active is not None:
            qs = qs.filter(active=(active.lower() == 'true'))

        return Response({
            'count'  : qs.count(),
            'results': RegleMetierSerializer(qs, many=True).data,
        })

    def post(self, request):
        roles = getattr(request.user, 'roles', [])
        if 'admin' not in roles:
            return Response(
                {'error': 'Réservé aux administrateurs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = RegleMetierCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        regle = serializer.save()
        tracer_action(request, 'CREATE', f'ia/regle/{regle.id}', details={
            'nom'    : regle.nom,
            'domaine': regle.domaine,
        })
        return Response(
            RegleMetierSerializer(regle).data,
            status=status.HTTP_201_CREATED
        )


class RegleMetierDetailView(APIView):
    """
    GET    /api/regles/{id}/  → détail
    PATCH  /api/regles/{id}/  → modifier (admin)
    DELETE /api/regles/{id}/  → supprimer (admin)
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request, pk):
        regle = get_object_or_404(RegleMetier, pk=pk)
        return Response(RegleMetierSerializer(regle).data)

    def patch(self, request, pk):
        regle      = get_object_or_404(RegleMetier, pk=pk)
        serializer = RegleMetierCreateSerializer(
            regle, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        tracer_action(request, 'UPDATE', f'ia/regle/{pk}', details=request.data)
        return Response(RegleMetierSerializer(regle).data)

    def delete(self, request, pk):
        regle = get_object_or_404(RegleMetier, pk=pk)
        nom_regle = regle.nom
        domaine_regle = regle.domaine
        regle.delete()
        tracer_action(request, 'DELETE', f'ia/regle/{pk}', details={
            'nom'    : nom_regle,
            'domaine': domaine_regle,
        })
        return Response(
            {'message': 'Règle supprimée.'},
            status=status.HTTP_204_NO_CONTENT
        )


class TesterRegleView(APIView):
    """
    POST /api/regles/{id}/tester/
    Teste une règle avec un contexte fourni.
    Utile pour l'admin avant de l'activer.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def post(self, request, pk):
        regle    = get_object_or_404(RegleMetier, pk=pk)
        contexte = request.data.get('contexte', {})

        if not isinstance(contexte, dict):
            return Response(
                {'error': 'contexte doit être un objet JSON.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .engine import NAMESPACE_SECURISE
            ns       = {**NAMESPACE_SECURISE, 'contexte': contexte}
            resultat = bool(eval(regle.condition, ns))
        except Exception as e:
            return Response({
                'regle_code': regle.code_regle,
                'condition' : regle.condition,
                'contexte'  : contexte,
                'resultat'  : False,
                'erreur'    : str(e),
            })

        return Response({
            'regle_code'  : regle.code_regle,
            'condition'   : regle.condition,
            'contexte'    : contexte,
            'resultat'    : resultat,
            'action'      : regle.action if resultat else None,
            'message'     : (
                f"La règle se déclenche → action : {regle.action}"
                if resultat
                else "La règle ne se déclenche pas."
            ),
        })


# ─────────────────────────────────────────────
#  DÉCISIONS AUTOMATIQUES
# ─────────────────────────────────────────────

class DecisionListView(APIView):
    """
    GET /api/decisions/
    Historique de toutes les décisions automatiques.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        qs = DecisionAutomatique.objects.all()

        # Filtres
        type_d      = request.query_params.get('type')
        etudiant    = request.query_params.get('etudiant_id')
        resultat    = request.query_params.get('resultat')
        date_debut  = request.query_params.get('date_debut')
        date_fin    = request.query_params.get('date_fin')

        if type_d:
            qs = qs.filter(type_decision=type_d)
        if etudiant:
            qs = qs.filter(etudiant_id=etudiant)
        if resultat:
            qs = qs.filter(resultat=resultat)
        if date_debut:
            qs = qs.filter(date_decision__date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_decision__date__lte=date_fin)

        limit  = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))

        return Response({
            'count'  : qs.count(),
            'results': DecisionAutomatiqueSerializer(
                qs[offset:offset + limit], many=True
            ).data,
        })


class DecisionDetailView(APIView):
    """GET /api/decisions/{id}/"""
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request, pk):
        decision = get_object_or_404(DecisionAutomatique, pk=pk)
        return Response(DecisionAutomatiqueSerializer(decision).data)


# ─────────────────────────────────────────────
#  ALERTES ANOMALIES
# ─────────────────────────────────────────────

class AlerteListView(APIView):
    """
    GET /api/alertes/
    Liste les alertes d'anomalies avec filtres.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        qs = AlerteAnomalie.objects.all()

        # Filtres
        type_a   = request.query_params.get('type')
        gravite  = request.query_params.get('gravite')
        statut   = request.query_params.get('statut')
        etudiant = request.query_params.get('etudiant_id')

        if type_a:
            qs = qs.filter(type_alerte=type_a)
        if gravite:
            qs = qs.filter(niveau_gravite=gravite)
        if statut:
            qs = qs.filter(statut_traitement=statut)
        if etudiant:
            qs = qs.filter(etudiant_id=etudiant)
        else:
            # Par défaut : alertes ouvertes uniquement
            if not request.query_params.get('tout'):
                qs = qs.filter(statut_traitement='ouverte')

        return Response({
            'count'   : qs.count(),
            'critiques': qs.filter(niveau_gravite='critique').count(),
            'results' : AlerteAnomalieSerializer(qs, many=True).data,
        })


class AlerteDetailView(APIView):
    """
    GET   /api/alertes/{id}/          → détail
    PATCH /api/alertes/{id}/resoudre/ → résoudre ou ignorer
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request, pk):
        alerte = get_object_or_404(AlerteAnomalie, pk=pk)
        return Response(AlerteAnomalieSerializer(alerte).data)


class ResoudreAlerteView(APIView):
    """PATCH /api/alertes/{id}/resoudre/"""
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def patch(self, request, pk):
        alerte     = get_object_or_404(AlerteAnomalie, pk=pk)
        serializer = ResoudreAlerteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        alerte.statut_traitement = serializer.validated_data['statut_traitement']
        alerte.note_resolution   = serializer.validated_data.get('note_resolution', '')
        alerte.resolu_par        = request.user.id
        alerte.date_resolution   = timezone.now()
        alerte.save()

        return Response({
            'message': f"Alerte {alerte.id} mise à jour.",
            'alerte' : AlerteAnomalieSerializer(alerte).data,
        })


# ─────────────────────────────────────────────
#  MOTEUR DÉCISION — STATUT
# ─────────────────────────────────────────────

class MoteurStatutView(APIView):
    """
    GET /api/moteur/statut/
    Retourne l'état du moteur de décision.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        moteur = MoteurDecision.objects.first()
        if not moteur:
            return Response({
                'statut'  : 'non_configure',
                'message' : 'Le moteur de décision n\'est pas configuré.',
            })
        return Response(MoteurDecisionSerializer(moteur).data)


# ─────────────────────────────────────────────
#  STATISTIQUES
# ─────────────────────────────────────────────

class StatistiquesIAView(APIView):
    """
    GET /api/statistiques/
    Tableau de bord du moteur IA.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        decisions = DecisionAutomatique.objects.all()
        alertes   = AlerteAnomalie.objects.all()
        regles    = RegleMetier.objects.all()

        from django.db.models import Count
        stats = {
            'regles': {
                'total' : regles.count(),
                'actives': regles.filter(active=True).count(),
                'par_domaine': {},
            },
            'decisions': {
                'total'     : decisions.count(),
                'par_type'  : {},
                'par_resultat': {},
            },
            'alertes': {
                'total'     : alertes.count(),
                'ouvertes'  : alertes.filter(statut_traitement='ouverte').count(),
                'critiques' : alertes.filter(niveau_gravite='critique').count(),
                'par_type'  : {},
            },
        }

        for domaine, _ in RegleMetier.DOMAINE_CHOICES:
            stats['regles']['par_domaine'][domaine] = regles.filter(
                domaine=domaine
            ).count()

        for type_d, _ in DecisionAutomatique.TYPE_CHOICES:
            stats['decisions']['par_type'][type_d] = decisions.filter(
                type_decision=type_d
            ).count()

        for res in decisions.values_list('resultat', flat=True).distinct():
            stats['decisions']['par_resultat'][res] = decisions.filter(
                resultat=res
            ).count()

        for type_a, _ in AlerteAnomalie.TYPE_CHOICES:
            stats['alertes']['par_type'][type_a] = alertes.filter(
                type_alerte=type_a
            ).count()

        return Response(stats)
