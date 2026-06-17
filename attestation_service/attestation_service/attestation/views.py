from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
import logging

from .models import DemandeAttestation, Attestation
from .serializers import (
    DemandeAttestationSerializer,
    DemandeListSerializer,
    SoumettreDemandeSerializer,
    AttestationSerializer,
)
from .permissions import (
    EstEtudiant, EstAgentScolarite,
    EstAgentOuAdmin, EstAdmin,
)
from .services import AttestationService
from .storage import generer_url_telechargement
from .utils import tracer_action

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  DEMANDES — ÉTUDIANT
# ─────────────────────────────────────────────

class SoumettreDemandeView(APIView):
    """
    POST /api/attestations/demandes/
    L'étudiant soumet une demande d'attestation.
    Le traitement est automatique et immédiat :
    vérification IA → génération PDF → stockage MinIO → notification.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def post(self, request):
        serializer = SoumettreDemandeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Éviter les demandes en double (même type + même année)
        annee = serializer.validated_data.get('annee_universitaire', '')
        type_att = serializer.validated_data['type_attestation']

        demande_existante = DemandeAttestation.objects.filter(
            etudiant_id         = request.user.etudiant_id,
            type_attestation    = type_att,
            annee_universitaire = annee,
            statut              = 'generee'
        ).first()

        if demande_existante:
            # Cas nominal: une attestation liée existe déjà.
            if Attestation.objects.filter(demande=demande_existante).exists():
                return Response(
                    {
                        'message' : 'Une attestation de ce type existe déjà.',
                        'demande' : DemandeAttestationSerializer(
                            demande_existante
                        ).data,
                    },
                    status=status.HTTP_200_OK
                )

            # Auto-réparation: statut générée sans objet Attestation lié.
            demande_existante.statut = 'approuvee'
            demande_existante.save(update_fields=['statut'])

            service = AttestationService()
            attestation = service.traiter_demande(
                demande_existante,
                authorization_header=request.headers.get('Authorization')
            )
            demande_existante.refresh_from_db()

            if attestation:
                return Response(
                    {
                        'message'    : (
                            'Attestation récupérée et générée avec succès. '
                            'Vous pouvez la télécharger maintenant.'
                        ),
                        'numero'     : attestation.numero_ordre,
                        'code_verif' : str(attestation.code_verification),
                        'demande'    : DemandeAttestationSerializer(
                            demande_existante
                        ).data,
                    },
                    status=status.HTTP_201_CREATED
                )

            return Response(
                {
                    'message' : (
                        'Une demande existe déjà mais le document est '
                        'incomplet. Contactez la scolarité pour régénération.'
                    ),
                    'demande' : DemandeAttestationSerializer(
                        demande_existante
                    ).data,
                },
                status=status.HTTP_409_CONFLICT
            )

        # Réutiliser une demande en_attente existante (pipeline précédent échoué)
        demande = DemandeAttestation.objects.filter(
            etudiant_id         = request.user.etudiant_id,
            type_attestation    = type_att,
            annee_universitaire = annee,
            statut              = 'en_attente',
        ).first()

        if not demande:
            demande = DemandeAttestation.objects.create(
                etudiant_id         = request.user.etudiant_id,
                type_attestation    = type_att,
                annee_universitaire = annee,
                motif               = serializer.validated_data.get('motif', ''),
            )
            tracer_action(request, 'SUBMIT', f'attestation/demande/{demande.id}', details={
                'type_attestation'  : type_att,
                'annee_universitaire': annee,
            })

        # Lancer le pipeline automatique
        service     = AttestationService()
        attestation = service.traiter_demande(
            demande,
            authorization_header=request.headers.get('Authorization')
        )

        demande.refresh_from_db()

        if attestation:
            tracer_action(request, 'GENERATE', f'attestation/{attestation.id}', details={
                'type_attestation': type_att,
                'numero_ordre'    : attestation.numero_ordre,
                'demande_id'      : demande.id,
            })
            return Response(
                {
                    'message'       : (
                        'Attestation générée avec succès. '
                        'Vous pouvez la télécharger maintenant.'
                    ),
                    'numero'        : attestation.numero_ordre,
                    'code_verif'    : str(attestation.code_verification),
                    'demande'       : DemandeAttestationSerializer(
                        demande
                    ).data,
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    'message'    : 'Demande traitée.',
                    'statut'     : demande.statut,
                    'motif_refus': demande.motif_refus,
                    'demande'    : DemandeAttestationSerializer(
                        demande
                    ).data,
                },
                status=status.HTTP_200_OK
            )


class MesDemandesView(APIView):
    """
    GET /api/attestations/mes-demandes/
    L'étudiant consulte toutes ses demandes et attestations.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        demandes = DemandeAttestation.objects.filter(
            etudiant_id=request.user.etudiant_id
        ).order_by('-date_demande')

        # Filtre optionnel par type
        type_att = request.query_params.get('type')
        if type_att:
            demandes = demandes.filter(type_attestation=type_att)

        return Response({
            'count'  : demandes.count(),
            'results': DemandeAttestationSerializer(
                demandes, many=True
            ).data,
        })


class MaDemandeDetailView(APIView):
    """
    GET /api/attestations/demandes/{id}/
    Détail d'une demande + attestation si générée.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request, pk):
        demande = get_object_or_404(
            DemandeAttestation,
            pk          = pk,
            etudiant_id = request.user.etudiant_id
        )
        return Response(
            DemandeAttestationSerializer(demande).data
        )


# ─────────────────────────────────────────────
#  TÉLÉCHARGEMENT
# ─────────────────────────────────────────────

class TelechargerAttestationView(APIView):
    """
    GET /api/attestations/{id}/telecharger/
    Génère une URL signée valable 5 minutes pour
    télécharger le PDF depuis MinIO.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        attestation = get_object_or_404(Attestation, pk=pk)

        # Vérifier accès
        roles = getattr(request.user, 'roles', [])
        if ('etudiant' in roles
                and request.user.etudiant_id
                    != attestation.demande.etudiant_id):
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not attestation.pdf_path:
            return Response(
                {'error': 'PDF non disponible.'},
                status=status.HTTP_404_NOT_FOUND
            )

        url = generer_url_telechargement(attestation.pdf_path)
        if not url:
            return Response(
                {'error': 'Erreur génération URL.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Marquer comme délivrée au premier téléchargement
        if attestation.statut_attestation == 'generee':
            attestation.statut_attestation = 'delivree'
            attestation.date_retrait       = timezone.now()
            attestation.save()

        tracer_action(request, 'DOWNLOAD', f'attestation/{pk}', details={
            'type_attestation': attestation.type_attestation,
            'numero_ordre'    : attestation.numero_ordre,
        })

        return Response({
            'url'        : url,
            'numero'     : attestation.numero_ordre,
            'type'       : attestation.type_attestation,
            'expiration' : '5 minutes',
        })


class RegenererAttestationView(APIView):
    """
    POST /api/attestations/demandes/{id}/regenerer/
    Regénère le PDF d'une attestation existante.
    Utile si le fichier est corrompu ou perdu.
    """
    permission_classes = [IsAuthenticated, EstAgentScolarite]

    def post(self, request, pk):
        demande = get_object_or_404(
            DemandeAttestation,
            pk     = pk,
            statut = 'generee'
        )
        service     = AttestationService()

        # Supprimer l'ancienne attestation
        try:
            demande.attestation.delete()
        except Exception:
            pass

        demande.statut = 'approuvee'
        demande.save()

        attestation = service.traiter_demande(
            demande,
            authorization_header=request.headers.get('Authorization')
        )
        if attestation:
            tracer_action(request, 'GENERATE', f'attestation/demande/{pk}', details={
                'numero_ordre': attestation.numero_ordre,
                'type_attestation': demande.type_attestation,
                'source': 'regeneration',
            })
            return Response({
                'message'   : 'Attestation regénérée.',
                'numero'    : attestation.numero_ordre,
            })
        return Response(
            {'error': 'Erreur lors de la regénération.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ─────────────────────────────────────────────
#  VÉRIFICATION PUBLIQUE
# ─────────────────────────────────────────────

class VerifierAttestationView(APIView):
    """
    GET /api/attestations/verifier/{code}/
    Endpoint PUBLIC — aucune authentification requise.
    Permet à n'importe qui (employeur, école, jury)
    de vérifier l'authenticité d'une attestation
    en scannant le QR code.
    """
    permission_classes = [AllowAny]

    def get(self, request, code):
        try:
            attestation = Attestation.objects.select_related(
                'demande'
            ).get(code_verification=code)

            return Response({
                'valide'            : True,
                'numero'            : attestation.numero_ordre,
                'type'              : attestation.get_type_attestation_display()
                    if hasattr(attestation, 'get_type_attestation_display')
                    else attestation.type_attestation,
                'annee_universitaire': attestation.annee_universitaire,
                'date_generation'   : attestation.date_generation,
                'statut'            : attestation.statut_attestation,
                'message'           : (
                    "Ce document est authentique et a été "
                    "émis par l'Université Alioune Diop de Bambey."
                ),
            })
        except Attestation.DoesNotExist:
            return Response(
                {
                    'valide' : False,
                    'message': (
                        "Ce document est introuvable ou invalide. "
                        "Il n'a pas été émis par l'UADB ou "
                        "le code de vérification est incorrect."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND
            )


# ─────────────────────────────────────────────
#  GESTION AGENTS / ADMIN
# ─────────────────────────────────────────────

class DemandeListAdminView(APIView):
    """
    GET /api/attestations/admin/demandes/
    Agents et admin : lister toutes les demandes avec filtres.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        qs = DemandeAttestation.objects.all().order_by('-date_demande')

        # Filtres
        statut   = request.query_params.get('statut')
        type_att = request.query_params.get('type')
        annee    = request.query_params.get('annee')
        etudiant = request.query_params.get('etudiant_id')

        if statut:
            qs = qs.filter(statut=statut)
        if type_att:
            qs = qs.filter(type_attestation=type_att)
        if annee:
            qs = qs.filter(annee_universitaire=annee)
        if etudiant:
            qs = qs.filter(etudiant_id=etudiant)

        serializer = DemandeListSerializer(qs, many=True)
        return Response({
            'count'  : qs.count(),
            'results': serializer.data,
        })


class DemandeDetailAdminView(APIView):
    """
    GET   /api/attestations/admin/demandes/{id}/  → détail
    PATCH /api/attestations/admin/demandes/{id}/  → traitement manuel
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request, pk):
        demande = get_object_or_404(DemandeAttestation, pk=pk)
        return Response(DemandeAttestationSerializer(demande).data)

    def patch(self, request, pk):
        """
        Traitement manuel d'une demande en attente.
        Permet à un agent de valider ou refuser manuellement.
        """
        demande = get_object_or_404(DemandeAttestation, pk=pk)

        if demande.statut not in ('en_attente', 'refusee'):
            return Response(
                {'error': 'Seules les demandes en attente peuvent être traitées.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        action = request.data.get('action')

        if action == 'approuver':
            service     = AttestationService()
            service.traiter_demande(
                demande,
                authorization_header=request.headers.get('Authorization')
            )
            demande.refresh_from_db()
            demande.traite_par = request.user.id
            demande.save()
            return Response({
                'message': 'Demande approuvée et attestation générée.',
                'demande': DemandeAttestationSerializer(demande).data,
            })

        elif action == 'refuser':
            motif = request.data.get('motif_refus', 'Refus manuel.')
            demande.statut      = 'refusee'
            demande.motif_refus = motif
            demande.traite_par  = request.user.id
            demande.date_traitement = timezone.now()
            demande.save()

            from .utils import notifier_etudiant
            notifier_etudiant(
                demande.etudiant_id,
                f"Votre demande d'attestation a été refusée. "
                f"Motif : {motif}"
            )
            return Response({
                'message': 'Demande refusée.',
                'demande': DemandeAttestationSerializer(demande).data,
            })

        return Response(
            {'error': "Action invalide. Utilisez 'approuver' ou 'refuser'."},
            status=status.HTTP_400_BAD_REQUEST
        )


class StatistiquesAttestationView(APIView):
    """
    GET /api/attestations/statistiques/
    Tableau de bord pour l'administration.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        annee = request.query_params.get(
            'annee',
            f"{timezone.now().year}-{timezone.now().year + 1}"
        )

        from django.db.models import Count
        qs = DemandeAttestation.objects.filter(
            annee_universitaire=annee
        )

        stats = {
            'annee'       : annee,
            'total'       : qs.count(),
            'par_statut'  : {},
            'par_type'    : {},
            'generees'    : Attestation.objects.filter(
                demande__annee_universitaire=annee
            ).count(),
        }

        for s in ('en_attente', 'approuvee', 'refusee', 'generee'):
            stats['par_statut'][s] = qs.filter(statut=s).count()

        for t, _ in DemandeAttestation.TYPE_CHOICES:
            stats['par_type'][t] = qs.filter(
                type_attestation=t
            ).count()

        return Response(stats)
