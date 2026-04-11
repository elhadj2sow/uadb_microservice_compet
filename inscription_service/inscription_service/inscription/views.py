from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
import json
import unicodedata
import requests
import logging

from .models import (Inscription, Paiement,
                     ValidationService, Workflow, EtapeWorkflow)
from .serializers import (
    InscriptionSerializer, InscriptionListSerializer,
    PreinscriptionSerializer, ValiderEtapeSerializer,
    PaiementSerializer, PaiementCreateSerializer,
    PaiementSoumissionSerializer,
    PayTechInitSerializer,
    PayTechWebhookSerializer,
    ValidationServiceSerializer,
)
from .permissions import (
    EstEtudiant, EstAgentScolarite, EstAgentComptable,
    EstAgentOuAdmin, EstAdmin,
)
from .signals import auto_valider_comptabilite_si_paiement_confirme

logger = logging.getLogger(__name__)

# Mapping rôle → service de validation
ROLE_SERVICE_MAP = {
    'agent_scolarite' : 'scolarite',
    'agent_comptable' : 'comptabilite',
    'service_medical' : 'medical',
    'bibliotheque'    : 'bibliotheque',
}

FRAIS_PAR_NIVEAU = {
    'L1': 25000,
    'L2': 25000,
    'L3': 25000,
    'M1': 50000,
    'M2': 50000,
}


def get_internal_token():
    try:
        res = requests.post(
            f"{settings.SERVICE_AUTH}/api/auth/login/",
            json={
                'username': settings.SERVICE_INTERNAL_USER,
                'password': settings.SERVICE_INTERNAL_PASSWORD,
            },
            timeout=5
        )
        return res.json().get('access', '')
    except Exception:
        return ''


def auth_header():
    token = get_internal_token()
    return {'Authorization': f'Bearer {token}'} if token else {}


def _get_formation(formation_id):
    """Récupère les informations de formation depuis dossier_service."""
    try:
        res = requests.get(
            f"{settings.SERVICE_DOSSIER}/api/formations/{formation_id}/",
            headers=auth_header(),
            timeout=5
        )
        if res.status_code != 200:
            return None
        return res.json()
    except Exception:
        return None


def _montant_attendu_inscription(inscription):
    """Calcule les frais d'inscription selon le niveau de la formation."""
    formation = _get_formation(inscription.formation_id)
    if not formation:
        return None

    niveau = formation.get('niveau')
    if niveau not in FRAIS_PAR_NIVEAU:
        return None

    return FRAIS_PAR_NIVEAU[niveau]


def _normaliser_decision(decision):
    if not decision:
        return ''
    value = str(decision).strip().lower()
    value = ''.join(
        c for c in unicodedata.normalize('NFKD', value)
        if not unicodedata.combining(c)
    )
    return value


def _annee_precedente(annee_universitaire):
    try:
        debut, fin = annee_universitaire.split('-')
        debut_i = int(debut)
        fin_i = int(fin)
        return f"{debut_i - 1}-{fin_i - 1}"
    except Exception:
        return None


def _statut_paytech_to_interne(statut_externe):
    statut = (statut_externe or '').strip().lower()
    if statut in {
        'paid', 'success', 'succeeded', 'completed',
        'approved', 'ok', 'done', 'sale_complete',
        'payment_success', 'successful'
    }:
        return 'confirme'
    if 'success' in statut or 'complete' in statut or 'paid' in statut:
        return 'confirme'
    if statut in {'partial', 'partially_paid'}:
        return 'partiel'
    if statut in {'refund', 'refunded', 'rembourse'}:
        return 'rembourse'
    return 'en_attente'


def _normaliser_redirect_url(url, fallback):
    value = (url or '').strip()
    if not value:
        value = (fallback or '').strip()

    # PayTech attend une URL publique et HTTPS pour la redirection.
    if value.lower().startswith('https://') and 'localhost' not in value.lower():
        return value

    return fallback


def _initier_paytech_transaction(*, inscription, paiement, success_url, cancel_url, target_payment=''):
    if not settings.PAYTECH_ENABLED:
        raise ValueError("PayTech est désactivé dans la configuration.")

    if not settings.PAYTECH_API_KEY or not settings.PAYTECH_API_SECRET:
        raise ValueError("Clés PayTech manquantes dans la configuration.")

    reference = (
        paiement.reference_paiement
        or f"INSC-{inscription.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    )

    ipn_url = settings.PAYTECH_WEBHOOK_URL
    success = _normaliser_redirect_url(
        success_url,
        settings.PAYTECH_SUCCESS_URL,
    )
    cancel = _normaliser_redirect_url(
        cancel_url,
        settings.PAYTECH_CANCEL_URL,
    )

    if not success:
        success = 'https://paytech.sn/mobile/success'
    if not cancel:
        cancel = 'https://paytech.sn/mobile/cancel'

    payload = {
        'item_name': f"Frais inscription {inscription.annee_universitaire}",
        'item_price': float(paiement.montant),
        'currency': 'XOF',
        'ref_command': reference,
        'command_name': f"Inscription {inscription.id}",
        'env': 'test' if settings.PAYTECH_SANDBOX else 'prod',
        'custom_field': json.dumps({
            'inscription_id': inscription.id,
            'etudiant_id': inscription.etudiant_id,
            'reference': reference,
        }),
    }

    if success:
        payload['success_url'] = success
    if cancel:
        payload['cancel_url'] = cancel
    if ipn_url and str(ipn_url).lower().startswith('https://'):
        payload['ipn_url'] = ipn_url
    if target_payment:
        payload['target_payment'] = target_payment

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'API_KEY': settings.PAYTECH_API_KEY,
        'API_SECRET': settings.PAYTECH_API_SECRET,
    }

    response = requests.post(
        f"{settings.PAYTECH_BASE_URL.rstrip('/')}/payment/request-payment",
        json=payload,
        headers=headers,
        timeout=20,
    )
    data = response.json() if response.content else {}

    if response.status_code >= 400:
        raise ValueError(
            data.get('message')
            or data.get('error')
            or "Erreur PayTech lors de l'initialisation du paiement."
        )

    payment_url = (
        data.get('redirect_url')
        or data.get('payment_url')
        or data.get('url')
    )
    token = data.get('token') or data.get('payment_token') or ''
    transaction_id = data.get('transaction_id') or data.get('id') or ''
    status_ext = data.get('status') or ''

    if not payment_url:
        raise ValueError("PayTech n'a pas retourné d'URL de paiement.")

    return {
        'reference': reference,
        'payment_url': payment_url,
        'token': token,
        'transaction_id': transaction_id,
        'status': status_ext,
        'raw': data,
    }


# ─────────────────────────────────────────────
#  ENDPOINTS ÉTUDIANT
# ─────────────────────────────────────────────

class PreinscriptionView(APIView):
    """
    POST /api/inscriptions/
    L'étudiant soumet sa demande de préinscription.
    Le signal demarrer_workflow() est déclenché automatiquement.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def post(self, request):
        serializer = PreinscriptionSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier complétude du dossier via service IA
        eligible, motif, dossier_id = self._verifier_dossier(
            request,
            serializer.validated_data.get('annee_universitaire')
        )
        if not eligible:
            return Response(
                {'error': f"Dossier incomplet : {motif}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Politique de reinscription basée sur la decision de delibération.
        type_inscription = serializer.validated_data.get(
            'type_inscription',
            'premiere'
        )
        annee_universitaire = serializer.validated_data.get('annee_universitaire')
        decision_ok, decision_message = self._verifier_reinscription(
            request,
            type_inscription,
            annee_universitaire,
        )
        if not decision_ok:
            return Response(
                {'error': decision_message},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Créer l'inscription → signal demarrer_workflow déclenché
        save_kwargs = {'etudiant_id': request.user.etudiant_id}
        if dossier_id:
            save_kwargs['dossier_id'] = dossier_id

        inscription = serializer.save(**save_kwargs)

        payload = InscriptionSerializer(inscription).data
        if decision_message:
            payload['message_condition'] = decision_message

        return Response(
            payload,
            status=status.HTTP_201_CREATED
        )

    def _verifier_dossier(self, request, annee_universitaire=None):
        """Appel au service IA pour vérifier complétude du dossier."""
        try:
            # Récupérer le score du dossier
            res_dossier = requests.get(
                f"{settings.SERVICE_DOSSIER}/api/dossiers/mon-dossier/",
                params={
                    'annee': annee_universitaire
                } if annee_universitaire else None,
                headers={'Authorization': request.META.get(
                    'HTTP_AUTHORIZATION', ''
                )},
                timeout=5
            )
            if res_dossier.status_code != 200:
                return False, (
                    "Aucun dossier trouvé pour l'année universitaire demandée."
                ), None

            score = res_dossier.json().get('score_completude', 0)
            dossier_id = res_dossier.json().get('id', 0)

            # Appel au moteur de règles
            res_ia = requests.post(
                f"{settings.SERVICE_IA}/api/evaluer/",
                json={
                    'type'       : 'completude_dossier',
                    'etudiant'   : request.user.etudiant_id,
                    'dossier_id' : dossier_id,
                    'score'      : score,
                },
                headers=auth_header(),
                timeout=5
            )
            data = res_ia.json()
            return (
                data.get('eligible', False),
                data.get('motif', ''),
                dossier_id,
            )
        except Exception as e:
            logger.warning(f"Vérification dossier ignorée : {e}")
            # En cas d'erreur réseau, on laisse passer
            return True, '', None

    def _verifier_reinscription(self, request, type_inscription, annee):
        if type_inscription != 'reinscription':
            return True, ''

        annee_prec = _annee_precedente(annee)
        if not annee_prec:
            return False, (
                "Année universitaire invalide pour la réinscription. "
                "Format attendu: YYYY-YYYY"
            )

        try:
            res = requests.get(
                f"{settings.SERVICE_DELIBERATION}/api/resultats/mes-resultats/",
                headers={
                    'Authorization': request.META.get('HTTP_AUTHORIZATION', '')
                },
                timeout=5
            )
            if res.status_code != 200:
                return False, (
                    "Impossible de vérifier votre décision de délibération "
                    "pour la réinscription."
                )

            resultats = res.json().get('results', [])
            cibles = [
                r for r in resultats
                if r.get('annee_universitaire') == annee_prec
            ]
            if not cibles:
                return False, (
                    f"Aucun résultat de délibération trouvé pour l'année {annee_prec}. "
                    "Réinscription impossible pour le moment."
                )

            cible = sorted(
                cibles,
                key=lambda r: (
                    1 if r.get('statut_deliberation') == 'cloturee' else 0,
                    r.get('semestre') or 0,
                ),
                reverse=True,
            )[0]
            decision = _normaliser_decision(cible.get('decision', ''))

            if decision == 'admis':
                return True, ''

            if decision == 'rattrapage':
                return True, (
                    "Réinscription conditionnelle autorisée: décision rattrapage. "
                    "Validation pédagogique complémentaire requise."
                )

            if decision in ('ajourne', 'exclu'):
                return False, (
                    "Réinscription refusée: décision de délibération "
                    f"'{cible.get('decision')}'."
                )

            return False, (
                "Réinscription impossible: décision de délibération "
                "non déterminée."
            )
        except Exception:
            return False, (
                "Erreur de vérification de la décision de délibération. "
                "Veuillez réessayer plus tard."
            )


class AutoCreateInscriptionView(APIView):
    """
    POST /api/inscriptions/auto-create/
    Endpoint interne pour créer automatiquement une inscription
    à partir d'un dossier validé.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roles = getattr(request.user, 'roles', [])
        username = getattr(request.user, 'username', '')
        if 'admin' not in roles and not username.startswith('service_'):
            return Response(
                {'error': 'Accès réservé aux services internes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        etudiant_id = request.data.get('etudiant_id')
        formation_id = request.data.get('formation_id')
        annee = request.data.get('annee_universitaire')
        type_inscription = request.data.get('type_inscription', 'premiere')
        dossier_id = request.data.get('dossier_id')

        if type_inscription == 'reinscription':
            return Response(
                {
                    'error': (
                        "La réinscription doit être initiée par l'étudiant "
                        "via l'endpoint de préinscription afin de vérifier "
                        "la décision de délibération."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not etudiant_id or not formation_id or not annee:
            return Response(
                {
                    'error': (
                        'etudiant_id, formation_id et '
                        'annee_universitaire sont obligatoires.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        existante = Inscription.objects.filter(
            etudiant_id=etudiant_id,
            annee_universitaire=annee
        ).first()
        if existante:
            return Response(
                {
                    'message': 'Inscription déjà existante pour cette année.',
                    'inscription': InscriptionSerializer(existante).data,
                },
                status=status.HTTP_200_OK
            )

        inscription = Inscription.objects.create(
            etudiant_id=etudiant_id,
            formation_id=formation_id,
            annee_universitaire=annee,
            type_inscription=type_inscription,
            dossier_id=dossier_id,
        )

        return Response(
            {
                'message': 'Inscription créée automatiquement.',
                'inscription': InscriptionSerializer(inscription).data,
            },
            status=status.HTTP_201_CREATED
        )


class MonInscriptionView(APIView):
    """
    GET /api/inscriptions/mon-inscription/?annee=2024-2025
    L'étudiant consulte son inscription avec le détail du workflow.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        annee = request.query_params.get(
            'annee', self._annee_courante()
        )
        inscription = get_object_or_404(
            Inscription,
            etudiant_id         = request.user.etudiant_id,
            annee_universitaire = annee
        )
        return Response(InscriptionSerializer(inscription).data)

    def _annee_courante(self):
        y = timezone.now().year
        return f"{y}-{y + 1}"


class MesInscriptionsView(APIView):
    """
    GET /api/inscriptions/mes-inscriptions/
    Historique de toutes les inscriptions de l'étudiant.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        inscriptions = Inscription.objects.filter(
            etudiant_id=request.user.etudiant_id
        ).order_by('-date_preinscription')
        serializer = InscriptionListSerializer(inscriptions, many=True)
        return Response({
            'count'  : inscriptions.count(),
            'results': serializer.data,
        })


# ─────────────────────────────────────────────
#  ENDPOINTS AGENTS / ADMINISTRATION
# ─────────────────────────────────────────────

class InscriptionListView(APIView):
    """
    GET /api/inscriptions/liste/
    Agent scolarité : liste toutes les inscriptions avec filtres.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        qs = Inscription.objects.all().order_by('-date_preinscription')

        # Filtres optionnels
        statut     = request.query_params.get('statut')
        annee      = request.query_params.get('annee')
        formation  = request.query_params.get('formation_id')
        etudiant   = request.query_params.get('etudiant_id')

        if statut:
            qs = qs.filter(statut_inscription=statut)
        if annee:
            qs = qs.filter(annee_universitaire=annee)
        if formation:
            qs = qs.filter(formation_id=formation)
        if etudiant:
            qs = qs.filter(etudiant_id=etudiant)

        serializer = InscriptionListSerializer(qs, many=True)
        return Response({
            'count'  : qs.count(),
            'results': serializer.data,
        })


class InscriptionDetailView(APIView):
    """
    GET /api/inscriptions/{id}/
    Détail complet d'une inscription — agents et admin.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request, pk):
        inscription = get_object_or_404(Inscription, pk=pk)
        return Response(InscriptionSerializer(inscription).data)


class ValiderEtapeView(APIView):
    """
    PATCH /api/inscriptions/{id}/valider-etape/
    Chaque service valide ou rejette sa propre étape.
    Le signal passer_etape_suivante() est déclenché automatiquement.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        inscription = get_object_or_404(Inscription, pk=pk)

        # Vérifier que l'inscription est en cours
        if inscription.statut_inscription not in ('en_cours', 'en_attente'):
            return Response(
                {'error': 'Cette inscription ne peut plus être modifiée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Identifier le service de l'agent connecté
        roles = getattr(request.user, 'roles', [])
        type_service = None
        for role, service in ROLE_SERVICE_MAP.items():
            if role in roles:
                type_service = service
                break

        if not type_service:
            if 'admin' not in roles:
                return Response(
                    {'error': 'Votre rôle ne vous permet pas de valider une étape.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Admin peut préciser le service dans le body
            type_service = request.data.get('type_service')
            if not type_service:
                return Response(
                    {'error': 'Précisez type_service dans le body.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Valider le serializer
        serializer = ValiderEtapeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        action      = serializer.validated_data['action']
        observation = serializer.validated_data.get('observation', '')

        # Pour l'etape comptabilite, imposer un paiement confirme et integral
        if type_service == 'comptabilite' and action == 'valider':
            paiement = Paiement.objects.filter(inscription=inscription).first()
            if not paiement:
                return Response(
                    {'error': 'Aucun paiement soumis pour cette inscription.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if paiement.statut_paiement != 'confirme':
                return Response(
                    {'error': 'Le paiement doit etre confirme par la comptabilite avant validation.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if paiement.montant_paye < paiement.montant:
                return Response(
                    {'error': 'Le montant paye est insuffisant pour valider cette etape.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Récupérer la ValidationService correspondante
        try:
            vs = ValidationService.objects.get(
                inscription_id    = inscription.id,
                type_service      = type_service,
                statut_validation = 'en_attente'
            )
        except ValidationService.DoesNotExist:
            return Response(
                {'error': (
                    f"Aucune étape en attente pour le service "
                    f"'{type_service}' sur cette inscription."
                )},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier que c'est bien l'étape courante
        etape_active = EtapeWorkflow.objects.filter(
            workflow__inscription = inscription,
            validation_service   = vs,
            statut               = 'en_cours'
        ).exists()

        if not etape_active:
            return Response(
                {'error': "Cette étape n'est pas encore active."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Appliquer la décision
        if action == 'valider':
            vs.statut_validation = 'valide'
        else:
            vs.statut_validation = 'rejete'

        vs.date_validation = timezone.now()
        vs.valide_par      = request.user.id
        vs.observation     = observation
        vs.save()
        # → signal passer_etape_suivante() déclenché automatiquement

        # Recharger l'inscription
        inscription.refresh_from_db()
        return Response({
            'message'     : (
                f"Étape '{type_service}' "
                f"{'validée' if action == 'valider' else 'rejetée'} avec succès."
            ),
            'inscription' : InscriptionSerializer(inscription).data,
        })


class StatutWorkflowView(APIView):
    """
    GET /api/inscriptions/{id}/workflow/
    État détaillé du circuit de validation.
    Accessible à l'étudiant concerné et aux agents.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        inscription = get_object_or_404(Inscription, pk=pk)

        # L'étudiant ne peut voir que sa propre inscription
        roles = getattr(request.user, 'roles', [])
        if 'etudiant' in roles and 'admin' not in roles:
            if request.user.etudiant_id != inscription.etudiant_id:
                return Response(
                    {'error': 'Accès refusé.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            wf    = inscription.workflow
            etapes = wf.etapes.all().order_by('ordre')
        except Workflow.DoesNotExist:
            return Response(
                {'error': 'Workflow introuvable pour cette inscription.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'inscription_id'   : inscription.id,
            'etudiant_id'      : inscription.etudiant_id,
            'statut_global'    : inscription.statut_inscription,
            'numero_provisoire': inscription.numero_provisoire,
            'numero_matricule' : inscription.numero_matricule,
            'workflow': {
                'id'            : wf.id,
                'statut'        : wf.statut,
                'etape_courante': wf.etape_courante,
                'progression'   : round(
                    etapes.filter(statut='validee').count() /
                    etapes.count() * 100
                ) if etapes.count() else 0,
                'etapes': [
                    {
                        'ordre'          : e.ordre,
                        'nom'            : e.nom_etape,
                        'service'        : e.validation_service.type_service,
                        'statut'         : e.statut,
                        'date_debut'     : e.date_debut,
                        'date_fin'       : e.date_fin,
                        'relances'       : e.relances_envoyees,
                    }
                    for e in etapes
                ],
            },
        })


# ─────────────────────────────────────────────
#  ENDPOINTS PAIEMENT
# ─────────────────────────────────────────────

class PaiementView(APIView):
    """
    GET   /api/inscriptions/{id}/paiement/  → consulter
    POST  /api/inscriptions/{id}/paiement/  → soumettre preuve (etudiant)
    PATCH /api/inscriptions/{id}/paiement/  → confirmer/enregistrer (comptable)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        inscription = get_object_or_404(Inscription, pk=pk)
        # Vérifier accès
        roles = getattr(request.user, 'roles', [])
        if ('etudiant' in roles
                and request.user.etudiant_id != inscription.etudiant_id):
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            return Response(PaiementSerializer(inscription.paiement).data)
        except Paiement.DoesNotExist:
            return Response(
                {'message': 'Aucun paiement enregistré.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, pk):
        # L'etudiant soumet sa preuve de paiement.
        roles = getattr(request.user, 'roles', [])
        if 'etudiant' not in roles:
            return Response(
                {'error': 'Réservé à l\'étudiant pour soumission de preuve.'},
                status=status.HTTP_403_FORBIDDEN
            )

        inscription = get_object_or_404(Inscription, pk=pk)
        if inscription.etudiant_id != request.user.etudiant_id:
            return Response(
                {'error': 'Vous ne pouvez soumettre le paiement que de votre inscription.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PaiementSoumissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        montant_attendu = _montant_attendu_inscription(inscription)
        if montant_attendu is None:
            return Response(
                {
                    'error': (
                        "Impossible de déterminer le montant d'inscription "
                        "pour cette formation."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        paiement, created = Paiement.objects.get_or_create(
            inscription=inscription,
            defaults={'montant': montant_attendu}
        )

        paiement.montant = montant_attendu

        if not created and paiement.statut_paiement == 'confirme':
            return Response(
                {'error': 'Ce paiement est deja confirme. Contactez la comptabilite en cas de correction.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        paiement.montant_paye      = serializer.validated_data['montant_paye']
        paiement.mode_paiement     = serializer.validated_data['mode_paiement']
        paiement.reference_paiement = serializer.validated_data.get(
            'reference_paiement', ''
        )
        paiement.recu_path         = serializer.validated_data.get('recu_path', '')
        paiement.statut_paiement   = 'en_attente'
        paiement.date_paiement     = timezone.now()
        paiement.date_confirmation = None
        paiement.confirme_par      = None
        paiement.save()

        return Response({
            'message' : 'Preuve de paiement soumise. En attente de validation comptable.',
            'montant_attendu': f"{montant_attendu:.2f}",
            'paiement': PaiementSerializer(paiement).data,
        }, status=status.HTTP_201_CREATED)

    def patch(self, request, pk):
        # Seul l'agent comptable ou admin confirme/enregistre la transaction.
        roles = getattr(request.user, 'roles', [])
        if 'agent_comptable' not in roles and 'admin' not in roles:
            return Response(
                {'error': 'Réservé à l\'agent comptable.'},
                status=status.HTTP_403_FORBIDDEN
            )

        inscription = get_object_or_404(Inscription, pk=pk)
        serializer = PaiementCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        montant_attendu = _montant_attendu_inscription(inscription)
        if montant_attendu is None:
            return Response(
                {
                    'error': (
                        "Impossible de déterminer le montant d'inscription "
                        "pour cette formation."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        paiement, _ = Paiement.objects.get_or_create(
            inscription=inscription,
            defaults={'montant': montant_attendu}
        )
        paiement.montant           = montant_attendu
        paiement.montant_paye      = serializer.validated_data['montant_paye']
        paiement.mode_paiement     = serializer.validated_data['mode_paiement']
        paiement.reference_paiement = serializer.validated_data.get(
            'reference_paiement', ''
        )
        paiement.statut_paiement   = (
            'confirme' if paiement.montant_paye >= paiement.montant else 'partiel'
        )
        paiement.date_paiement     = paiement.date_paiement or timezone.now()
        paiement.date_confirmation = timezone.now()
        paiement.confirme_par      = request.user.id
        paiement.save()

        return Response({
            'message' : 'Paiement enregistre et traite par la comptabilite.',
            'paiement': PaiementSerializer(paiement).data,
        })


class PayTechInitPaiementView(APIView):
    """
    POST /api/inscriptions/{id}/paiement/paytech/initier/
    Initialise un paiement en ligne PayTech et retourne l'URL de redirection.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        inscription = get_object_or_404(Inscription, pk=pk)

        roles = getattr(request.user, 'roles', [])
        if ('etudiant' in roles
                and request.user.etudiant_id != inscription.etudiant_id):
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PayTechInitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        montant_attendu = _montant_attendu_inscription(inscription)
        if montant_attendu is None:
            return Response(
                {
                    'error': (
                        "Impossible de déterminer le montant d'inscription "
                        "pour cette formation."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        paiement, _ = Paiement.objects.get_or_create(
            inscription=inscription,
            defaults={'montant': montant_attendu}
        )

        if paiement.statut_paiement == 'confirme':
            return Response(
                {
                    'error': 'Ce paiement est déjà confirmé.',
                    'paiement': PaiementSerializer(paiement).data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        paiement.montant = montant_attendu
        paiement.mode_paiement = 'paytech'
        paiement.provider = 'paytech'
        paiement.statut_paiement = 'en_attente'

        try:
            init_data = _initier_paytech_transaction(
                inscription=inscription,
                paiement=paiement,
                success_url=serializer.validated_data.get('success_url'),
                cancel_url=serializer.validated_data.get('cancel_url'),
                target_payment=serializer.validated_data.get('target_payment', ''),
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.warning(f"Erreur initiation PayTech inscription={pk}: {e}")
            return Response(
                {'error': 'Erreur technique lors de l\'initiation du paiement.'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        paiement.reference_paiement = init_data['reference']
        paiement.payment_url = init_data['payment_url']
        paiement.transaction_token = init_data['token']
        paiement.transaction_id = init_data['transaction_id']
        paiement.statut_externe = init_data['status']
        paiement.callback_payload = init_data['raw']
        paiement.date_paiement = timezone.now()
        paiement.save()

        return Response(
            {
                'message': 'Session PayTech initialisée.',
                'payment_url': paiement.payment_url,
                'reference_paiement': paiement.reference_paiement,
                'transaction_token': paiement.transaction_token,
                'paiement': PaiementSerializer(paiement).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PayTechWebhookView(APIView):
    """
    POST /api/paiements/paytech/webhook/
    Callback serveur-à-serveur de PayTech.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        if hasattr(request.data, 'dict'):
            payload = request.data.dict()
        elif isinstance(request.data, dict):
            payload = request.data
        else:
            payload = {}
        serializer = PayTechWebhookSerializer(data=payload)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        reference = serializer.validated_data['reference_resolue']

        try:
            paiement = Paiement.objects.select_related('inscription').get(
                reference_paiement=reference
            )
        except Paiement.DoesNotExist:
            return Response(
                {'error': 'Référence de paiement inconnue.'},
                status=status.HTTP_404_NOT_FOUND
            )

        status_ext = serializer.validated_data.get('status_resolu', '')
        paiement_status = _statut_paytech_to_interne(status_ext)

        paiement.provider = 'paytech'
        paiement.mode_paiement = 'paytech'
        paiement.statut_externe = status_ext
        paiement.transaction_id = serializer.validated_data.get(
            'transaction_id', paiement.transaction_id
        )
        paiement.transaction_token = serializer.validated_data.get(
            'token', paiement.transaction_token
        )
        paiement.callback_payload = payload
        paiement.date_callback = timezone.now()

        montant_callback = serializer.validated_data.get('amount')
        if montant_callback is not None:
            paiement.montant_paye = montant_callback

        paiement.statut_paiement = paiement_status
        if paiement_status == 'confirme':
            if montant_callback is None or paiement.montant_paye < paiement.montant:
                # Certains callbacks PayTech ne renvoient pas le montant ; on
                # crédite alors le montant attendu à la confirmation.
                paiement.montant_paye = paiement.montant
            paiement.date_confirmation = timezone.now()
            paiement.date_paiement = paiement.date_paiement or timezone.now()

        paiement.save()

        if paiement_status == 'confirme':
            auto_valider_comptabilite_si_paiement_confirme(
                paiement.inscription_id
            )

        return Response(
            {
                'message': 'Callback PayTech traité.',
                'reference_paiement': paiement.reference_paiement,
                'statut_paiement': paiement.statut_paiement,
            },
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────
#  ENDPOINTS ADMINISTRATION / STATS
# ─────────────────────────────────────────────

class StatistiquesView(APIView):
    """
    GET /api/inscriptions/statistiques/
    Tableau de bord pour l'administration.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        annee = request.query_params.get(
            'annee',
            f"{timezone.now().year}-{timezone.now().year + 1}"
        )
        qs = Inscription.objects.filter(annee_universitaire=annee)

        stats = {
            'annee'          : annee,
            'total'          : qs.count(),
            'par_statut'     : {},
            'par_formation'  : {},
            'workflow_moyen' : 0,
        }

        for s in ['en_attente','en_cours','validee','rejetee','annulee']:
            stats['par_statut'][s] = qs.filter(
                statut_inscription=s
            ).count()

        # Formations les plus demandées
        from django.db.models import Count
        formations = qs.values('formation_id').annotate(
            nb=Count('id')
        ).order_by('-nb')[:5]
        stats['par_formation'] = list(formations)

        return Response(stats)


class EtapesBloqueeView(APIView):
    """
    GET /api/workflows/etapes-bloquees/
    Appelé par le service IA pour détecter les retards.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        maintenant     = timezone.now()
        etapes_retard  = []

        etapes = EtapeWorkflow.objects.filter(
            statut     = 'en_cours',
            date_debut__isnull = False
        ).select_related(
            'workflow__inscription',
            'validation_service'
        )

        for etape in etapes:
            delta  = maintenant - etape.date_debut
            heures = delta.total_seconds() / 3600
            if heures > etape.delai_max_heures:
                etapes_retard.append({
                    'etape_id'       : etape.id,
                    'nom_etape'      : etape.nom_etape,
                    'type_service'   : etape.validation_service.type_service,
                    'inscription_id' : etape.workflow.inscription_id,
                    'etudiant_id'    : etape.workflow.inscription.etudiant_id,
                    'heures_ecoulees': round(heures, 1),
                    'delai_max'      : etape.delai_max_heures,
                    'relances'       : etape.relances_envoyees,
                })

        return Response(etapes_retard)
