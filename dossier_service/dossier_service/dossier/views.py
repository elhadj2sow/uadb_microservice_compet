from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
import requests
import logging
import threading

from .models import (Formation, UniteEnseignement,
                     DossierEtudiant, PieceJustificative)
from .serializers import (
    FormationSerializer, FormationListSerializer,
    UniteEnseignementSerializer,
    DossierEtudiantSerializer, DossierListSerializer,
    CreerDossierSerializer,
    PieceJustificativeSerializer,
    DepotPieceSerializer, VerifierPieceSerializer,
)
from .permissions import (
    EstEtudiant, EstAgentScolarite,
    EstAgentOuAdmin, EstAdmin,
    EstAdminOuResponsablePedagogique,
)
from .storage import (
    uploader_fichier, supprimer_fichier,
    generer_url_telechargement,
)
from .utils import tracer_action

logger = logging.getLogger(__name__)


def _get_internal_token():
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


def _auth_header():
    token = _get_internal_token()
    return {'Authorization': f'Bearer {token}'} if token else {}


def _notifier_decision_dossier(dossier, etat, observation=''):
    """Envoie une notification email à l'étudiant (non-bloquant)."""
    if etat == 'valide':
        message = (
            "Bonne nouvelle ! Votre dossier d'inscription a été validé par l'administration. "
            "Votre inscription est en cours de traitement."
        )
        sujet = "Dossier validé"
    else:
        raison = f" Motif : {observation}" if observation else ""
        message = (
            f"Votre dossier d'inscription a été rejeté par l'administration.{raison} "
            "Veuillez corriger les éléments signalés et soumettre à nouveau."
        )
        sujet = "Dossier rejeté"
    payload = {
        'etudiant_id': dossier.etudiant_id,
        'canal'      : 'email',
        'sujet'      : sujet,
        'message'    : message,
    }
    def _send():
        try:
            requests.post(
                f"{settings.SERVICE_NOTIFICATION}/api/notifications/",
                json=payload, headers=_auth_header(), timeout=5,
            )
        except Exception as e:
            logger.warning(f"Notification décision dossier {dossier.id} échouée : {e}")
    threading.Thread(target=_send, daemon=True).start()


def _notifier_decision_piece(piece, action, motif=''):
    """Envoie une notification email à l'étudiant (non-bloquant)."""
    libelle = piece.type_piece.replace('_', ' ').capitalize()
    if action == 'valider':
        message = f"Votre pièce « {libelle} » a été validée par l'agent de scolarité."
        sujet   = f"Pièce validée : {libelle}"
    else:
        raison  = f" Motif : {motif}" if motif else ""
        message = (
            f"Votre pièce « {libelle} » a été rejetée.{raison} "
            "Veuillez déposer une nouvelle version dans votre espace."
        )
        sujet = f"Pièce rejetée : {libelle}"
    payload = {
        'etudiant_id': piece.dossier.etudiant_id,
        'canal'      : 'email',
        'sujet'      : sujet,
        'message'    : message,
    }
    def _send():
        try:
            requests.post(
                f"{settings.SERVICE_NOTIFICATION}/api/notifications/",
                json=payload, headers=_auth_header(), timeout=5,
            )
        except Exception as e:
            logger.warning(f"Notification décision pièce {piece.id} échouée : {e}")
    threading.Thread(target=_send, daemon=True).start()


def _creer_inscription_automatique(dossier):
    """Crée l'inscription via inscription_service à partir d'un dossier validé."""
    deja_inscrit_historiquement = DossierEtudiant.objects.filter(
        etudiant_id=dossier.etudiant_id
    ).exclude(pk=dossier.pk).exists()

    # Pour une réinscription, l'étudiant doit initier la demande manuellement
    # afin d'appliquer la politique de décision de délibération.
    if deja_inscrit_historiquement:
        logger.info(
            "Auto-création ignorée dossier=%s etudiant=%s (historique détecté)",
            dossier.id,
            dossier.etudiant_id,
        )
        return

    try:
        res = requests.post(
            f"{settings.SERVICE_INSCRIPTION}/api/inscriptions/auto-create/",
            json={
                'etudiant_id': dossier.etudiant_id,
                'formation_id': dossier.formation_id,
                'annee_universitaire': dossier.annee_universitaire,
                'type_inscription': 'premiere',
                'dossier_id': dossier.id,
            },
            headers=_auth_header(),
            timeout=5
        )
        if res.status_code not in (200, 201):
            logger.warning(
                "Auto-création inscription échouée dossier=%s status=%s body=%s",
                dossier.id,
                res.status_code,
                res.text,
            )
    except Exception as e:
        logger.warning(
            "Erreur auto-création inscription dossier=%s : %s",
            dossier.id,
            e,
        )


# ─────────────────────────────────────────────
#  FORMATIONS
# ─────────────────────────────────────────────

class FormationListView(APIView):
    """
    GET /api/formations/
    Liste toutes les formations actives.
    Accessible à tous les utilisateurs connectés.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Formation.objects.filter(actif=True)

        # Filtres
        niveau = request.query_params.get('niveau')
        if niveau:
            qs = qs.filter(niveau=niveau)

        serializer = FormationListSerializer(qs, many=True)
        return Response({
            'count'  : qs.count(),
            'results': serializer.data,
        })


class FormationDetailView(APIView):
    """
    GET /api/formations/{id}/
    Détail d'une formation avec toutes ses UE.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        formation = get_object_or_404(Formation, pk=pk, actif=True)
        return Response(FormationSerializer(formation).data)


class FormationCreateView(APIView):
    """
    POST  /api/formations/creer/  → créer une formation
    PATCH /api/formations/{id}/   → modifier (admin)
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def post(self, request):
        serializer = FormationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        formation = serializer.save()
        tracer_action(request, 'CREATE', f'formation/{formation.id}', details={
            'libelle': formation.libelle,
            'niveau' : getattr(formation, 'niveau', None),
        })
        return Response(
            FormationSerializer(formation).data,
            status=status.HTTP_201_CREATED
        )

    def patch(self, request, pk):
        formation  = get_object_or_404(Formation, pk=pk)
        serializer = FormationSerializer(
            formation, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        tracer_action(request, 'UPDATE', f'formation/{pk}', details=request.data)
        return Response(serializer.data)


class UECreateView(APIView):
    """
    POST /api/formations/{pk}/ues/creer/
    Crée une UE pour une formation donnée. Réservé à l'admin.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def post(self, request, pk):
        formation = get_object_or_404(Formation, pk=pk)
        data = request.data.copy()
        serializer = UniteEnseignementSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(formation=formation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UEDetailView(APIView):
    """
    PATCH /api/formations/{pk}/ues/{ue_pk}/modifier/
    DELETE /api/formations/{pk}/ues/{ue_pk}/supprimer/
    Réservé à l'admin.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get_ue(self, pk, ue_pk):
        return get_object_or_404(UniteEnseignement, pk=ue_pk, formation_id=pk)

    def patch(self, request, pk, ue_pk):
        ue = self.get_ue(pk, ue_pk)
        serializer = UniteEnseignementSerializer(ue, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk, ue_pk):
        ue = self.get_ue(pk, ue_pk)
        ue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UniteEnseignementListView(APIView):
    """
    GET /api/formations/{id}/ues/
    Liste les UE d'une formation par semestre.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        formation = get_object_or_404(Formation, pk=pk)
        semestre  = request.query_params.get('semestre')
        qs = UniteEnseignement.objects.filter(
            formation=formation, actif=True
        )
        if semestre:
            try:
                semestre = int(semestre)
            except (TypeError, ValueError):
                return Response(
                    {
                        'error': "Le paramètre semestre doit être un entier "
                                 "(ex: ?semestre=1)."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            qs = qs.filter(semestre=semestre)
        return Response({
            'formation': formation.libelle,
            'count'    : qs.count(),
            'ues'      : UniteEnseignementSerializer(qs, many=True).data,
        })


# ─────────────────────────────────────────────
#  DOSSIER ÉTUDIANT
# ─────────────────────────────────────────────

class CreerDossierView(APIView):
    """
    POST /api/dossiers/
    L'étudiant crée son dossier administratif.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def post(self, request):
        serializer = CreerDossierSerializer(
            data    = request.data,
            context = {'request': request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        dossier = serializer.save(
            etudiant_id = request.user.etudiant_id
        )
        logger.info(
            f"Dossier créé — étudiant {request.user.etudiant_id} "
            f"— formation {dossier.formation_id}"
        )
        tracer_action(request, 'CREATE', f'dossier/{dossier.id}', details={
            'formation_id'       : dossier.formation_id,
            'annee_universitaire': dossier.annee_universitaire,
        })
        return Response(
            DossierEtudiantSerializer(dossier).data,
            status=status.HTTP_201_CREATED
        )


class MonDossierView(APIView):
    """
    GET /api/dossiers/mon-dossier/
    L'étudiant consulte son dossier avec les pièces
    déposées, les pièces manquantes et le score de complétude.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        annee = request.query_params.get(
            'annee', self._annee_courante()
        )
        try:
            dossier = DossierEtudiant.objects.get(
                etudiant_id         = request.user.etudiant_id,
                annee_universitaire = annee
            )
        except DossierEtudiant.DoesNotExist:
            return Response(
                {
                    'message': 'Aucun dossier trouvé pour cette année.',
                    'annee'  : annee,
                },
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(DossierEtudiantSerializer(dossier).data)

    def _annee_courante(self):
        y = timezone.now().year
        return f"{y}-{y + 1}"


class MesDossiersView(APIView):
    """
    GET /api/dossiers/mes-dossiers/
    Historique de tous les dossiers de l'étudiant.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        dossiers = DossierEtudiant.objects.filter(
            etudiant_id=request.user.etudiant_id
        ).order_by('-date_creation')
        return Response(
            DossierListSerializer(dossiers, many=True).data
        )


class DossierListView(APIView):
    """
    GET /api/dossiers/liste/
    Agent scolarité : liste tous les dossiers avec filtres.
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        qs = DossierEtudiant.objects.all().order_by('-date_creation')

        # Filtres
        etat       = request.query_params.get('etat')
        annee      = request.query_params.get('annee')
        formation  = request.query_params.get('formation_id')
        etudiant   = request.query_params.get('etudiant_id')
        score_min  = request.query_params.get('score_min')

        if etat:
            qs = qs.filter(etat_dossier=etat)
        if annee:
            qs = qs.filter(annee_universitaire=annee)
        if formation:
            qs = qs.filter(formation_id=formation)
        if etudiant:
            qs = qs.filter(etudiant_id=etudiant)
        if score_min:
            qs = qs.filter(score_completude__gte=int(score_min))

        serializer = DossierListSerializer(qs, many=True)
        return Response({
            'count'  : qs.count(),
            'results': serializer.data,
        })


class DossierDetailView(APIView):
    """
    GET   /api/dossiers/{id}/  → détail complet
    PATCH /api/dossiers/{id}/  → valider/rejeter (agent)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        dossier = get_object_or_404(DossierEtudiant, pk=pk)

        # L'étudiant ne voit que son propre dossier
        roles = getattr(request.user, 'roles', [])
        if ('etudiant' in roles
                and request.user.etudiant_id != dossier.etudiant_id):
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(DossierEtudiantSerializer(dossier).data)

    def patch(self, request, pk):
        """Agent valide ou rejette le dossier complet."""
        roles = getattr(request.user, 'roles', [])
        if 'agent_scolarite' not in roles and 'admin' not in roles:
            return Response(
                {'error': 'Réservé aux agents de scolarité.'},
                status=status.HTTP_403_FORBIDDEN
            )

        dossier = get_object_or_404(DossierEtudiant, pk=pk)
        etat    = request.data.get('etat_dossier')

        if etat not in ('valide', 'rejete'):
            return Response(
                {'error': "etat_dossier doit être 'valide' ou 'rejete'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ancien_etat           = dossier.etat_dossier
        dossier.etat_dossier  = etat
        dossier.observation   = request.data.get('observation', '')
        dossier.valide_par    = request.user.id

        if etat == 'valide':
            dossier.date_validation = timezone.now().date()

        dossier.save()

        if etat == 'valide':
            _creer_inscription_automatique(dossier)

        tracer_action(
            request,
            'VALIDATE' if etat == 'valide' else 'REJECT',
            f'dossier/{pk}',
            details={
                'ancien_etat' : ancien_etat,
                'nouvel_etat' : etat,
                'observation' : dossier.observation,
            }
        )

        _notifier_decision_dossier(dossier, etat, dossier.observation)

        logger.info(
            f"Dossier {pk} : {ancien_etat} → {etat} "
            f"par agent {request.user.id}"
        )
        return Response(DossierEtudiantSerializer(dossier).data)


class DossierIncompletListView(APIView):
    """
    GET /api/dossiers/incomplets/
    Endpoint interne — appelé par le service IA
    pour détecter les pièces expirées.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .signals import PIECES_OBLIGATOIRES

        dossiers = DossierEtudiant.objects.filter(
            etat_dossier__in=('en_cours', 'incomplet')
        ).prefetch_related('pieces')

        resultats = []
        for d in dossiers:
            pieces_info = []
            for piece in d.pieces.all():
                pieces_info.append({
                    'id'             : piece.id,
                    'type_piece'     : piece.type_piece,
                    'statut'         : piece.statut_verification,
                    'est_expiree'    : piece.est_expiree,
                    'date_expiration': str(piece.date_expiration)
                        if piece.date_expiration else None,
                })
            resultats.append({
                'id'            : d.id,
                'etudiant_id'   : d.etudiant_id,
                'score'         : d.score_completude,
                'etat'          : d.etat_dossier,
                'pieces'        : pieces_info,
            })

        return Response(resultats)


# ─────────────────────────────────────────────
#  PIÈCES JUSTIFICATIVES
# ─────────────────────────────────────────────

class DeposerPieceView(APIView):
    """
    POST /api/dossiers/{id}/pieces/
    L'étudiant dépose une pièce justificative.
    Le fichier est uploadé sur MinIO.
    Le signal recalculer_completude() est déclenché.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def post(self, request, pk):
        dossier = get_object_or_404(
            DossierEtudiant,
            pk          = pk,
            etudiant_id = request.user.etudiant_id
        )

        serializer = DepotPieceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        fichier         = serializer.validated_data['fichier']
        type_piece      = serializer.validated_data['type_piece']
        est_obligatoire = serializer.validated_data['est_obligatoire']
        date_expiration = serializer.validated_data.get('date_expiration')

        # Upload sur MinIO
        chemin = uploader_fichier(
            fichier,
            request.user.etudiant_id,
            type_piece
        )
        if not chemin:
            return Response(
                {'error': 'Erreur lors de l\'upload du fichier.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Supprimer l'ancienne pièce du même type si elle existe
        ancienne = dossier.pieces.filter(type_piece=type_piece).first()
        if ancienne:
            supprimer_fichier(ancienne.chemin_stockage)
            ancienne.delete()

        # Créer la pièce en base
        piece = PieceJustificative.objects.create(
            dossier             = dossier,
            type_piece          = type_piece,
            nom_fichier         = fichier.name,
            chemin_stockage     = chemin,
            taille_fichier      = fichier.size,
            type_mime           = fichier.content_type,
            statut_verification = 'en_attente',
            est_obligatoire     = est_obligatoire,
            date_expiration     = date_expiration,
        )
        # → signal recalculer_completude() déclenché automatiquement

        tracer_action(request, 'UPLOAD', f'dossier/{pk}/piece/{piece.id}', details={
            'type_piece'    : type_piece,
            'nom_fichier'   : fichier.name,
            'est_obligatoire': est_obligatoire,
        })

        logger.info(
            f"Pièce déposée — dossier {pk} — "
            f"type : {type_piece} — chemin : {chemin}"
        )

        return Response(
            PieceJustificativeSerializer(piece).data,
            status=status.HTTP_201_CREATED
        )


class PiecesListView(APIView):
    """
    GET /api/dossiers/{id}/pieces/
    Liste toutes les pièces d'un dossier.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        dossier = get_object_or_404(DossierEtudiant, pk=pk)

        # Vérifier accès
        roles = getattr(request.user, 'roles', [])
        if ('etudiant' in roles
                and request.user.etudiant_id != dossier.etudiant_id):
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        pieces = dossier.pieces.all().order_by('type_piece')
        return Response({
            'dossier_id'     : dossier.id,
            'score_completude': dossier.score_completude,
            'count'          : pieces.count(),
            'pieces'         : PieceJustificativeSerializer(
                pieces, many=True
            ).data,
        })


class VerifierPieceView(APIView):
    """
    PATCH /api/pieces/{id}/verifier/
    Agent scolarité valide ou rejette une pièce.
    Le signal recalculer_completude() est déclenché automatiquement.
    """
    permission_classes = [IsAuthenticated, EstAgentScolarite]

    def patch(self, request, pk):
        piece      = get_object_or_404(PieceJustificative, pk=pk)
        serializer = VerifierPieceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        action      = serializer.validated_data['action']
        motif_rejet = serializer.validated_data.get('motif_rejet', '')

        ancien_statut = piece.statut_verification

        if action == 'valider':
            piece.statut_verification = 'valide'
            piece.motif_rejet         = ''
        else:
            piece.statut_verification = 'rejete'
            piece.motif_rejet         = motif_rejet

        piece.date_verification = timezone.now()
        piece.verifie_par       = request.user.id
        piece.save()
        # → signal recalculer_completude() déclenché automatiquement

        tracer_action(
            request,
            'VALIDATE' if action == 'valider' else 'REJECT',
            f'piece/{pk}',
            details={
                'ancien_statut': ancien_statut,
                'type_piece'   : piece.type_piece,
                'motif_rejet'  : motif_rejet,
            }
        )

        _notifier_decision_piece(piece, action, motif_rejet)

        logger.info(
            f"Pièce {pk} : {ancien_statut} → "
            f"{piece.statut_verification} "
            f"par agent {request.user.id}"
        )

        return Response({
            'message': (
                f"Pièce {'validée' if action == 'valider' else 'rejetée'}."
            ),
            'piece'  : PieceJustificativeSerializer(piece).data,
        })


class TelechargerPieceView(APIView):
    """
    GET /api/pieces/{id}/telecharger/
    Génère une URL signée pour télécharger le fichier depuis MinIO.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        piece = get_object_or_404(PieceJustificative, pk=pk)

        # Vérifier accès
        roles = getattr(request.user, 'roles', [])
        if ('etudiant' in roles
                and request.user.etudiant_id != piece.dossier.etudiant_id):
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        url = generer_url_telechargement(piece.chemin_stockage)
        if not url:
            return Response(
                {'error': 'Impossible de générer l\'URL de téléchargement.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        tracer_action(request, 'DOWNLOAD', f'piece/{pk}', details={
            'nom_fichier' : piece.nom_fichier,
            'type_piece'  : piece.type_piece,
            'dossier_id'  : piece.dossier_id,
        })
        return Response({
            'url'         : url,
            'nom_fichier' : piece.nom_fichier,
            'type_mime'   : piece.type_mime,
            'expiration'  : '5 minutes',
        })


class SupprimerPieceView(APIView):
    """
    DELETE /api/pieces/{id}/
    L'étudiant supprime une pièce rejetée pour la re-déposer.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def delete(self, request, pk):
        piece = get_object_or_404(PieceJustificative, pk=pk)

        # Vérifier que c'est bien l'étudiant propriétaire
        if request.user.etudiant_id != piece.dossier.etudiant_id:
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Autoriser la suppression seulement si rejetée ou en_attente
        if piece.statut_verification == 'valide':
            return Response(
                {'error': 'Impossible de supprimer une pièce déjà validée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Supprimer de MinIO
        dossier_id = piece.dossier_id
        piece_id   = piece.id
        type_piece = piece.type_piece
        supprimer_fichier(piece.chemin_stockage)
        piece.delete()

        tracer_action(request, 'DELETE', f'piece/{piece_id}', details={
            'dossier_id': dossier_id,
            'type_piece': type_piece,
        })

        return Response(
            {'message': 'Pièce supprimée avec succès.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ─────────────────────────────────────────────
#  STATISTIQUES (ADMIN)
# ─────────────────────────────────────────────

class StatistiquesDossierView(APIView):
    """
    GET /api/dossiers/statistiques/
    Tableau de bord pour l'administration et responsables pédagogiques.
    """
    permission_classes = [IsAuthenticated, EstAdminOuResponsablePedagogique]

    def get(self, request):
        annee = request.query_params.get(
            'annee',
            f"{timezone.now().year}-{timezone.now().year + 1}"
        )
        qs = DossierEtudiant.objects.filter(annee_universitaire=annee)

        from django.db.models import Count, Avg
        stats = {
            'annee'          : annee,
            'total'          : qs.count(),
            'par_etat'       : {},
            'score_moyen'    : 0,
            'complets'       : 0,
            'incomplets'     : 0,
        }

        for etat in ('en_cours', 'incomplet', 'complet', 'valide', 'rejete'):
            stats['par_etat'][etat] = qs.filter(etat_dossier=etat).count()

        if qs.exists():
            stats['score_moyen'] = round(
                qs.aggregate(m=Avg('score_completude'))['m'] or 0, 1
            )
        stats['complets']   = qs.filter(score_completude=100).count()
        stats['incomplets'] = qs.filter(score_completude__lt=100).count()

        return Response(stats)
