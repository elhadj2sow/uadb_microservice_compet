from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
import logging

from .models import Deliberation, Resultat, Note
from .serializers import (
    DeliberationSerializer, DeliberationListSerializer,
    CreerDeliberationSerializer, CloturerDeliberationSerializer,
    ResultatSerializer, ResultatListSerializer,
    ValiderResultatSerializer,
    NoteSerializer, SaisirNoteSerializer, SaisirNotesBulkSerializer,
)
from .permissions import (
    EstEtudiant, EstEnseignant, EstResponsablePedagogique,
    EstJuryOuAdmin, EstAdmin,
)
from .utils import (
    notifier_etudiant,
    get_unites_formation,
    appeler_moteur_regles,
    tracer_action,
)
from .pv_generator import generer_pv_deliberation

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  DÉLIBÉRATIONS
# ─────────────────────────────────────────────

class DeliberationListView(APIView):
    """
    GET  /api/deliberations/       → lister
    POST /api/deliberations/       → créer (responsable pédagogique)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Deliberation.objects.all().order_by('-date_creation')

        # Filtres
        annee      = request.query_params.get('annee')
        semestre   = request.query_params.get('semestre')
        formation  = request.query_params.get('formation_id')
        statut     = request.query_params.get('statut')
        session    = request.query_params.get('session')

        if annee:
            qs = qs.filter(annee_universitaire=annee)
        if semestre:
            qs = qs.filter(semestre=semestre)
        if formation:
            qs = qs.filter(formation_id=formation)
        if statut:
            qs = qs.filter(statut=statut)
        if session:
            qs = qs.filter(session=session)

        serializer = DeliberationListSerializer(qs, many=True)
        return Response({
            'count'  : qs.count(),
            'results': serializer.data,
        })

    def post(self, request):
        roles = getattr(request.user, 'roles', [])
        if ('responsable_pedagogique' not in roles
                and 'admin' not in roles):
            return Response(
                {'error': 'Réservé aux responsables pédagogiques.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CreerDeliberationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        deliberation = serializer.save()
        logger.info(f"Délibération {deliberation.id} créée.")
        tracer_action(request, 'CREATE', f'deliberation/{deliberation.id}', details={
            'annee_universitaire': deliberation.annee_universitaire,
            'formation_id'       : deliberation.formation_id,
            'semestre'           : deliberation.semestre,
            'session'            : deliberation.session,
        })
        return Response(
            DeliberationSerializer(deliberation).data,
            status=status.HTTP_201_CREATED
        )


class DeliberationDetailView(APIView):
    """
    GET   /api/deliberations/{id}/  → détail complet
    PATCH /api/deliberations/{id}/  → modifier
    """
    permission_classes = [IsAuthenticated, EstJuryOuAdmin]

    def get(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)
        return Response(DeliberationSerializer(deliberation).data)

    def patch(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)
        if deliberation.statut == 'cloturee':
            return Response(
                {'error': 'Impossible de modifier une délibération clôturée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = CreerDeliberationSerializer(
            deliberation, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        tracer_action(request, 'UPDATE', f'deliberation/{pk}', details=request.data)
        return Response(DeliberationSerializer(deliberation).data)

    def delete(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)
        roles = getattr(request.user, 'roles', [])
        if 'responsable_pedagogique' not in roles and 'admin' not in roles:
            return Response(
                {'error': 'Réservé aux responsables pédagogiques.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if deliberation.statut != 'en_preparation':
            return Response(
                {'error': 'Seules les délibérations en préparation peuvent être supprimées.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        annee_univ = deliberation.annee_universitaire
        formation_id = deliberation.formation_id
        deliberation.delete()
        tracer_action(request, 'DELETE', f'deliberation/{pk}', details={
            'annee_universitaire': annee_univ,
            'formation_id'       : formation_id,
        })
        return Response(status=status.HTTP_204_NO_CONTENT)


class DemarrerDeliberationView(APIView):
    """
    POST /api/deliberations/{id}/demarrer/
    Passe la délibération de 'en_preparation' à 'en_cours'.
    Permet aux enseignants de commencer la saisie des notes.
    Réservé au responsable pédagogique / admin.
    """
    permission_classes = [IsAuthenticated, EstResponsablePedagogique]

    def post(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)

        if deliberation.statut != 'en_preparation':
            return Response(
                {'error': 'Seule une délibération «en préparation» peut être démarrée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not deliberation.resultats.exists():
            return Response(
                {'error': 'Ajoutez au moins un étudiant avant de démarrer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deliberation.statut = 'en_cours'
        deliberation.save(update_fields=['statut'])
        logger.info(f"Délibération {deliberation.id} démarrée.")
        tracer_action(request, 'WORKFLOW_START', f'deliberation/{pk}', details={
            'annee_universitaire': deliberation.annee_universitaire,
            'formation_id'       : deliberation.formation_id,
            'semestre'           : deliberation.semestre,
        })
        return Response({'message': 'Délibération démarrée.', 'statut': 'en_cours'})


class CloturerDeliberationView(APIView):
    """
    POST /api/deliberations/{id}/cloturer/
    Clôture la délibération :
    - verrouille toutes les notes
    - calcule les rangs
    - notifie tous les étudiants
    - Réservé au responsable pédagogique / admin
    """
    permission_classes = [IsAuthenticated, EstResponsablePedagogique]

    def post(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)

        if deliberation.statut == 'cloturee':
            return Response(
                {'error': 'Cette délibération est déjà clôturée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CloturerDeliberationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Auto-calculer les décisions encore en attente
        resultats_a_traiter = deliberation.resultats.filter(
            moyenne_annuelle__isnull=False,
            decision='en_attente'
        )
        for resultat in resultats_a_traiter:
            decision_data = appeler_moteur_regles(
                moyenne=resultat.moyenne_annuelle,
                credits=resultat.credits_valides,
                etudiant_id=resultat.etudiant_id,
                deliberation_id=deliberation.id,
            )
            resultat.decision = decision_data.get('decision', resultat.decision)
            resultat.mention = decision_data.get('mention', resultat.mention)
            resultat.save(update_fields=['decision', 'mention'])

        # 2. Verrouiller toutes les notes
        Note.objects.filter(
            resultat__deliberation=deliberation
        ).update(verrouille=True)

        # 3. Calculer les rangs selon moyenne décroissante
        resultats = deliberation.resultats.filter(
            moyenne_annuelle__isnull=False
        ).order_by('-moyenne_annuelle')

        for rang, r in enumerate(resultats, start=1):
            Resultat.objects.filter(pk=r.pk).update(rang=rang)

        # 4. Mettre à jour la délibération
        deliberation.statut         = 'cloturee'
        deliberation.date_cloture   = timezone.now()
        deliberation.decision_finale = serializer.validated_data.get(
            'decision_finale', ''
        )
        deliberation.observation    = serializer.validated_data.get(
            'observation', ''
        )
        deliberation.save()

        # 5. Notifier tous les étudiants
        for r in deliberation.resultats.all():
            decision_label = dict(Resultat.DECISION_CHOICES).get(
                r.decision, r.decision
            )
            moy_str = (
                f"{float(r.moyenne_annuelle):.2f}/20"
                if r.moyenne_annuelle else 'N/A'
            )
            notifier_etudiant(
                r.etudiant_id,
                f"Les résultats de la délibération S{deliberation.semestre} "
                f"({deliberation.annee_universitaire}) sont disponibles. "
                f"Votre décision : {decision_label}. "
                f"Moyenne : {moy_str}."
            )

        logger.info(
            f"Délibération {pk} clôturée — "
            f"{deliberation.resultats.count()} résultats"
        )
        tracer_action(request, 'WORKFLOW_END', f'deliberation/{pk}', details={
            'annee_universitaire': deliberation.annee_universitaire,
            'formation_id'       : deliberation.formation_id,
            'nb_resultats'       : deliberation.resultats.count(),
        })
        return Response({
            'message'    : 'Délibération clôturée avec succès.',
            'deliberation': DeliberationSerializer(deliberation).data,
        })


class PVDeliberationView(APIView):
    """
    GET /api/deliberations/{id}/pv/
    Génère et télécharge le PV de délibération en PDF.
    """
    permission_classes = [IsAuthenticated, EstJuryOuAdmin]

    def get(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)

        if deliberation.statut != 'cloturee':
            return Response(
                {'error': 'Le PV n\'est disponible qu\'après clôture.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        buffer = generer_pv_deliberation(deliberation)
        if not buffer:
            return Response(
                {'error': 'Erreur lors de la génération du PV.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        nom_fichier = (
            f"PV_S{deliberation.semestre}_"
            f"{deliberation.annee_universitaire}_"
            f"{deliberation.session}.pdf"
        )
        response = HttpResponse(
            buffer.read(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{nom_fichier}"'
        )
        return response


# ─────────────────────────────────────────────
#  RÉSULTATS
# ─────────────────────────────────────────────

class ResultatListView(APIView):
    """
    GET  /api/deliberations/{id}/resultats/ → lister
    POST /api/deliberations/{id}/resultats/ → ajouter un étudiant
    """
    permission_classes = [IsAuthenticated, EstJuryOuAdmin]

    def get(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)
        resultats    = deliberation.resultats.all().order_by(
            'rang', 'etudiant_id'
        )

        # Filtre optionnel par décision
        decision = request.query_params.get('decision')
        if decision:
            resultats = resultats.filter(decision=decision)

        return Response({
            'deliberation_id': deliberation.id,
            'statut'         : deliberation.statut,
            'count'          : resultats.count(),
            'results'        : ResultatListSerializer(
                resultats, many=True
            ).data,
        })

    def post(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)

        if deliberation.statut == 'cloturee':
            return Response(
                {'error': 'Délibération clôturée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        etudiant_id    = request.data.get('etudiant_id')
        inscription_id = request.data.get('inscription_id')

        if not etudiant_id:
            return Response(
                {'error': 'etudiant_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier doublon
        if Resultat.objects.filter(
            deliberation=deliberation,
            etudiant_id=etudiant_id
        ).exists():
            return Response(
                {'error': 'Cet étudiant est déjà dans cette délibération.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        resultat = Resultat.objects.create(
            deliberation   = deliberation,
            etudiant_id    = etudiant_id,
            inscription_id = inscription_id,
            credits_total  = request.data.get('credits_total', 60),
        )
        tracer_action(request, 'CREATE', f'deliberation/{pk}/resultat/{resultat.id}', details={
            'etudiant_id'  : etudiant_id,
            'inscription_id': inscription_id,
        })
        return Response(
            ResultatSerializer(resultat).data,
            status=status.HTTP_201_CREATED
        )


class ResultatDetailView(APIView):
    """
    GET   /api/resultats/{id}/  → détail avec toutes les notes
    PATCH /api/resultats/{id}/  → jury modifie la décision
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        resultat = get_object_or_404(Resultat, pk=pk)

        # L'étudiant ne voit que son propre résultat
        roles = getattr(request.user, 'roles', [])
        if 'etudiant' in roles:
            if request.user.id != resultat.etudiant_id:
                return Response(
                    {'error': 'Accès refusé.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return Response(ResultatSerializer(resultat).data)

    def patch(self, request, pk):
        """Jury modifie manuellement la décision d'un étudiant."""
        roles = getattr(request.user, 'roles', [])
        if ('responsable_pedagogique' not in roles
                and 'enseignant' not in roles
                and 'admin' not in roles):
            return Response(
                {'error': 'Accès réservé aux membres du jury.'},
                status=status.HTTP_403_FORBIDDEN
            )

        resultat   = get_object_or_404(Resultat, pk=pk)
        serializer = ValiderResultatSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        resultat.decision        = serializer.validated_data['decision']
        resultat.mention         = serializer.validated_data.get('mention', '')
        resultat.observation     = serializer.validated_data.get('observation', '')
        resultat.rang            = serializer.validated_data.get('rang')
        resultat.valide_par      = request.user.id
        resultat.date_validation = timezone.now()
        resultat.save()

        tracer_action(request, 'VALIDATE', f'resultat/{pk}', details={
            'decision'   : resultat.decision,
            'mention'    : resultat.mention,
            'etudiant_id': resultat.etudiant_id,
        })

        return Response(ResultatSerializer(resultat).data)


class MesResultatsView(APIView):
    """
    GET /api/resultats/mes-resultats/
    L'étudiant consulte tous ses résultats de délibération.
    """
    permission_classes = [IsAuthenticated, EstEtudiant]

    def get(self, request):
        resultats = Resultat.objects.filter(
            etudiant_id=request.user.id
        ).select_related('deliberation').prefetch_related('notes').order_by(
            '-deliberation__annee_universitaire',
            'deliberation__semestre'
        )

        data = []
        for r in resultats:
            notes = r.notes.all().order_by('semestre', 'code_ue')
            data.append({
                'id'                 : r.id,
                'annee_universitaire': r.deliberation.annee_universitaire,
                'semestre'           : r.deliberation.semestre,
                'session'            : r.deliberation.session,
                'niveau'             : r.deliberation.niveau,
                'moyenne_annuelle'   : r.moyenne_annuelle,
                'credits_valides'    : r.credits_valides,
                'credits_total'      : r.credits_total,
                'decision'           : r.decision,
                'mention'            : r.mention,
                'rang'               : r.rang,
                'statut_deliberation': r.deliberation.statut,
                'notes'              : [
                    {
                        'ue_id'      : n.ue_id,
                        'code_ue'    : n.code_ue,
                        'libelle_ue' : n.libelle_ue,
                        'semestre'   : n.semestre,
                        'credit'     : n.credit_ue,
                        'valeur'     : n.valeur,
                    }
                    for n in notes
                ],
            })
        return Response({'count': len(data), 'results': data})


# ─────────────────────────────────────────────
#  NOTES
# ─────────────────────────────────────────────

class SaisirNoteView(APIView):
    """
    POST /api/resultats/{id}/notes/
    Enseignant saisit les notes d'un étudiant pour une UE.
    Le signal recalculer_moyenne() est déclenché automatiquement.
    """
    permission_classes = [IsAuthenticated, EstEnseignant]

    def post(self, request, pk):
        resultat = get_object_or_404(Resultat, pk=pk)
        deliberation = resultat.deliberation

        if deliberation.statut == 'cloturee':
            return Response(
                {'error': 'Impossible de saisir des notes après clôture.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SaisirNoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data   = serializer.validated_data
        ue_id  = data['ue_id']

        # UE dans le référentiel de la formation (dossier_service)
        ues    = get_unites_formation(deliberation.formation_id)
        ue_ref = next((u for u in ues if u.get('id') == ue_id), None)

        # Si dossier_service est injoignable, on utilise les données du payload
        if not ue_ref and not ues:
            ue_ref = {
                'id'         : ue_id,
                'code_ue'    : data.get('code_ue', ''),
                'libelle_ue' : data.get('libelle_ue', ''),
                'credit'     : data.get('credit_ue', 3),
                'coefficient': float(data.get('coefficient_ue', 1.0)),
                'semestre'   : data.get('semestre', 1),
            }
        elif not ue_ref:
            # dossier_service répond mais l'UE n'est pas dans cette formation
            return Response(
                {
                    'error': (
                        f"L'UE {ue_id} n'appartient pas à la formation "
                        f"{deliberation.formation_id}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Créer ou mettre à jour la note
        note, created = Note.objects.get_or_create(
            resultat = resultat,
            ue_id    = ue_id,
            defaults = {
                'code_ue'       : ue_ref.get('code_ue', ''),
                'libelle_ue'    : ue_ref.get('libelle_ue', ''),
                'credit_ue'     : ue_ref.get('credit', 3),
                'coefficient_ue': ue_ref.get('coefficient', 1.0),
                'semestre'      : ue_ref.get('semestre', 1),
                'saisi_par'     : request.user.id,
            }
        )

        if not created and note.verrouille:
            return Response(
                {'error': 'Cette note est verrouillée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Conserver les métadonnées UE alignées sur le référentiel officiel
        note.code_ue        = ue_ref.get('code_ue', note.code_ue)
        note.libelle_ue     = ue_ref.get('libelle_ue', note.libelle_ue)
        note.credit_ue      = ue_ref.get('credit', note.credit_ue)
        note.coefficient_ue = ue_ref.get('coefficient', note.coefficient_ue)
        note.semestre       = ue_ref.get('semestre', note.semestre)

        # Mettre à jour les valeurs
        note.note_cc         = data.get('note_cc')
        note.note_tp         = data.get('note_tp')
        note.note_examen     = data.get('note_examen')
        note.note_rattrapage = data.get('note_rattrapage')
        note.type_evaluation = data.get('type_evaluation', '')
        note.saisi_par       = request.user.id
        note.save()
        # → signal recalculer_moyenne() déclenché automatiquement

        tracer_action(
            request,
            'CREATE' if created else 'UPDATE',
            f'resultat/{pk}/note/{note.id}',
            details={
                'ue_id'    : ue_id,
                'code_ue'  : note.code_ue,
                'note_cc'  : note.note_cc,
                'note_examen': note.note_examen,
                'etudiant_id': resultat.etudiant_id,
            }
        )

        action = "créée" if created else "mise à jour"
        return Response(
            {
                'message': f"Note {action} avec succès.",
                'note'   : NoteSerializer(note).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class SaisirNotesBulkView(APIView):
    """
    POST /api/deliberations/{id}/notes/bulk/
    Saisir les notes de plusieurs étudiants en une seule requête.
    Utile pour importer un fichier Excel de notes.
    """
    permission_classes = [IsAuthenticated, EstEnseignant]

    def post(self, request, pk):
        deliberation = get_object_or_404(Deliberation, pk=pk)

        if deliberation.statut == 'cloturee':
            return Response(
                {'error': 'Délibération clôturée.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SaisirNotesBulkSerializer(
            data=request.data, many=True
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        nb_traitees = 0
        erreurs     = []

        # Charger une seule fois le référentiel UE de la formation
        ues = get_unites_formation(deliberation.formation_id)
        ue_map = {ue.get('id'): ue for ue in ues}

        for item in serializer.validated_data:
            etudiant_id = item['etudiant_id']
            try:
                resultat, _ = Resultat.objects.get_or_create(
                    deliberation = deliberation,
                    etudiant_id  = etudiant_id,
                    defaults     = {'credits_total': 60}
                )
                for note_data in item['notes']:
                    ue_ref = ue_map.get(note_data['ue_id'])
                    if not ue_ref:
                        erreurs.append({
                            'etudiant_id': etudiant_id,
                            'ue_id': note_data['ue_id'],
                            'erreur': (
                                f"UE hors référentiel formation "
                                f"{deliberation.formation_id}"
                            ),
                        })
                        continue

                    note, _ = Note.objects.get_or_create(
                        resultat = resultat,
                        ue_id    = note_data['ue_id'],
                        defaults = {
                            'code_ue'       : ue_ref.get('code_ue', ''),
                            'libelle_ue'    : ue_ref.get('libelle_ue', ''),
                            'credit_ue'     : ue_ref.get('credit', 3),
                            'coefficient_ue': ue_ref.get('coefficient', 1.0),
                            'semestre'      : ue_ref.get('semestre', 1),
                        }
                    )
                    if not note.verrouille:
                        note.code_ue       = ue_ref.get('code_ue', note.code_ue)
                        note.libelle_ue    = ue_ref.get('libelle_ue', note.libelle_ue)
                        note.credit_ue     = ue_ref.get('credit', note.credit_ue)
                        note.coefficient_ue = ue_ref.get('coefficient', note.coefficient_ue)
                        note.semestre      = ue_ref.get('semestre', note.semestre)
                        note.note_cc      = note_data.get('note_cc')
                        note.note_tp      = note_data.get('note_tp')
                        note.note_examen  = note_data.get('note_examen')
                        note.saisi_par    = request.user.id
                        note.save()
                        nb_traitees += 1
            except Exception as e:
                erreurs.append({
                    'etudiant_id': etudiant_id,
                    'erreur'     : str(e)
                })

        tracer_action(request, 'CREATE', f'deliberation/{pk}/notes/bulk', details={
            'nb_traitees'   : nb_traitees,
            'nb_erreurs'    : len(erreurs),
            'formation_id'  : deliberation.formation_id,
            'annee'         : deliberation.annee_universitaire,
        })
        return Response({
            'message'    : f"{nb_traitees} notes saisies.",
            'nb_traitees': nb_traitees,
            'erreurs'    : erreurs,
        })


class NotesEtudiantView(APIView):
    """
    GET /api/resultats/{id}/notes/
    Toutes les notes d'un résultat étudiant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        resultat = get_object_or_404(Resultat, pk=pk)

        # Vérifier accès
        roles = getattr(request.user, 'roles', [])
        if ('etudiant' in roles
                and request.user.id != resultat.etudiant_id):
            return Response(
                {'error': 'Accès refusé.'},
                status=status.HTTP_403_FORBIDDEN
            )

        notes = resultat.notes.all().order_by('semestre', 'code_ue')
        return Response({
            'resultat_id'    : resultat.id,
            'etudiant_id'    : resultat.etudiant_id,
            'moyenne_annuelle': resultat.moyenne_annuelle,
            'decision'       : resultat.decision,
            'count'          : notes.count(),
            'notes'          : NoteSerializer(notes, many=True).data,
        })


# ─────────────────────────────────────────────
#  STATISTIQUES
# ─────────────────────────────────────────────

class StatistiquesDeliberationView(APIView):
    """
    GET /api/deliberations/statistiques/
    Tableau de bord pour l'administration.
    """
    permission_classes = [IsAuthenticated, EstJuryOuAdmin]

    def get(self, request):
        annee = request.query_params.get(
            'annee',
            f"{timezone.now().year}-{timezone.now().year + 1}"
        )
        delibs = Deliberation.objects.filter(
            annee_universitaire=annee
        )
        resultats = Resultat.objects.filter(
            deliberation__annee_universitaire=annee
        )

        from django.db.models import Avg, Count
        stats = {
            'annee'              : annee,
            'nb_deliberations'   : delibs.count(),
            'nb_etudiants_total' : resultats.count(),
            'par_decision'       : {},
            'moyenne_generale'   : 0,
            'taux_reussite'      : 0,
        }

        for dec in ('admis', 'rattrapage', 'ajourné', 'exclu', 'en_attente'):
            stats['par_decision'][dec] = resultats.filter(
                decision=dec
            ).count()

        if resultats.filter(moyenne_annuelle__isnull=False).exists():
            moy = resultats.filter(
                moyenne_annuelle__isnull=False
            ).aggregate(m=Avg('moyenne_annuelle'))['m']
            stats['moyenne_generale'] = round(float(moy or 0), 2)

        total = resultats.count()
        if total:
            admis = resultats.filter(decision='admis').count()
            stats['taux_reussite'] = round((admis / total) * 100, 1)

        return Response(stats)
