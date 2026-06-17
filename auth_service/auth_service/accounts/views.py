from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Utilisateur, Etudiant, Role, JournalAudit
from .serializers import (
    CustomTokenSerializer,
    RegisterEtudiantSerializer,
    UtilisateurSerializer,
    UtilisateurListSerializer,
    ChangePasswordSerializer,
    UpdateProfilSerializer,
    JournalAuditSerializer,
    AssignerRoleSerializer,
    EtudiantSerializer,
)
from .permissions import EstAdmin, EstEtudiant, EstAgentOuAdmin
from .utils import tracer_action


# ─────────────────────────────────────────────
#  AUTHENTIFICATION
# ─────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Retourne access token + refresh token.
    Trace la connexion dans JournalAudit.
    """
    permission_classes = [AllowAny]
    serializer_class   = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Tracer la connexion réussie
            try:
                user = Utilisateur.objects.get(
                    username=request.data.get('username', '')
                )
                tracer_action(
                    request,
                    action    = 'LOGIN',
                    ressource = 'auth/login',
                    utilisateur = user,
                    details   = {'method': 'jwt'}
                )
            except Exception:
                pass
        else:
            # Tracer la tentative de connexion échouée
            try:
                tracer_action(
                    request,
                    action      = 'LOGIN_ECHEC',
                    ressource   = 'auth/login',
                    utilisateur = None,
                    details     = {
                        'username'   : request.data.get('username', ''),
                        'statut_http': response.status_code,
                    },
                    statut      = 'echec',
                    niveau      = 'WARNING',
                )
            except Exception:
                pass
        return response


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blackliste le refresh token.
    Trace la déconnexion dans JournalAudit.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Le refresh token est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            tracer_action(
                request,
                action    = 'LOGOUT',
                ressource = 'auth/logout',
            )
            return Response(
                {'message': 'Déconnexion réussie.'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Token invalide ou déjà révoqué.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RegisterEtudiantView(APIView):
    """
    POST /api/auth/register/
    Créer un compte étudiant complet.
    Crée Utilisateur + profil Etudiant + rôle 'etudiant'.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterEtudiantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.save()
        tracer_action(
            request,
            action      = 'CREATE',
            ressource   = f'auth/utilisateur/{user.id}',
            utilisateur = user,
            details     = {
                'type'     : 'inscription_etudiant',
                'username' : user.username,
            }
        )
        return Response(
            {
                'message'  : 'Compte créé avec succès.',
                'username' : user.username,
                'email'    : user.email,
            },
            status=status.HTTP_201_CREATED
        )


# ─────────────────────────────────────────────
#  PROFIL UTILISATEUR CONNECTÉ
# ─────────────────────────────────────────────

class MeView(APIView):
    """
    GET   /api/auth/me/  → Profil complet
    PATCH /api/auth/me/  → Mise à jour du profil étudiant
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        try:
            etudiant = request.user.etudiant
        except Etudiant.DoesNotExist:
            return Response(
                {'error': 'Profil étudiant introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UpdateProfilSerializer(
            etudiant,
            data    = request.data,
            partial = True
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        tracer_action(
            request,
            action    = 'UPDATE',
            ressource = f'auth/etudiant/{etudiant.id}',
            details   = {'champs_modifies': list(request.data.keys())}
        )
        return Response(
            {'message': 'Profil mis à jour.', 'profil': serializer.data}
        )


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Changement de mot de passe par l'utilisateur connecté.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        if not user.check_password(
            serializer.validated_data['ancien_password']
        ):
            return Response(
                {'error': 'Ancien mot de passe incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data['nouveau_password'])
        user.save()
        tracer_action(
            request,
            action    = 'RESET_PWD',
            ressource = f'auth/utilisateur/{user.id}',
        )
        return Response(
            {'message': 'Mot de passe modifié avec succès.'}
        )


# ─────────────────────────────────────────────
#  GESTION UTILISATEURS (ADMIN)
# ─────────────────────────────────────────────

class UtilisateurListView(APIView):
    """
    GET /api/auth/utilisateurs/
    Liste tous les utilisateurs avec filtres.
    Réservé aux admins.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        qs = Utilisateur.objects.all().order_by('-date_joined')

        # Filtres
        role  = request.query_params.get('role')
        etat  = request.query_params.get('etat')
        search = request.query_params.get('search')

        if role:
            qs = qs.filter(roles__libelle=role)
        if etat:
            qs = qs.filter(etat_compte=etat)
        if search:
            qs = qs.filter(username__icontains=search) | \
                 qs.filter(email__icontains=search)

        serializer = UtilisateurListSerializer(qs, many=True)
        return Response({
            'count'  : qs.count(),
            'results': serializer.data,
        })


class UtilisateurDetailView(APIView):
    """
    GET   /api/auth/utilisateurs/{id}/  → Détail
    PATCH /api/auth/utilisateurs/{id}/  → Modifier etat_compte
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request, pk):
        user = get_object_or_404(Utilisateur, pk=pk)
        return Response(UtilisateurSerializer(user).data)

    def patch(self, request, pk):
        user = get_object_or_404(Utilisateur, pk=pk)
        ancien_etat = user.etat_compte

        etat = request.data.get('etat_compte')
        if etat not in ('actif', 'inactif', 'bloque', 'suspendu'):
            return Response(
                {'error': 'Valeur etat_compte invalide.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.etat_compte = etat
        user.save()
        tracer_action(
            request,
            action    = 'UPDATE',
            ressource = f'auth/utilisateur/{user.id}',
            details   = {
                'ancien_etat' : ancien_etat,
                'nouveau_etat': etat,
            }
        )
        return Response(
            {'message': f'Compte {user.username} mis à jour.',
             'etat_compte': user.etat_compte}
        )


class AssignerRoleView(APIView):
    """
    POST /api/auth/utilisateurs/{id}/roles/
    Ajouter ou retirer un rôle à un utilisateur.
    Réservé aux admins.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def post(self, request, pk):
        user       = get_object_or_404(Utilisateur, pk=pk)
        serializer = AssignerRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        libelle = serializer.validated_data['role']
        action  = serializer.validated_data['action']

        try:
            role = Role.objects.get(libelle=libelle)
        except Role.DoesNotExist:
            return Response(
                {'error': f"Rôle '{libelle}' inexistant."},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == 'ajouter':
            user.roles.add(role)
            msg = f"Rôle '{libelle}' ajouté à {user.username}."
        else:
            user.roles.remove(role)
            msg = f"Rôle '{libelle}' retiré de {user.username}."

        tracer_action(
            request,
            action    = 'UPDATE',
            ressource = f'auth/utilisateur/{user.id}/roles',
            details   = {'role': libelle, 'operation': action}
        )
        return Response({
            'message': msg,
            'roles'  : user.role_list,
        })


class MettreAJourMatriculeView(APIView):
    """
    PATCH /api/auth/etudiants/{id}/matricule/
    Appelé par le service inscription après validation du workflow.
    Met à jour le matricule définitif de l'étudiant.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        # Seul un service interne (admin) peut appeler cet endpoint
        roles = getattr(request.user, 'role_list',
                        [] if not request.user.is_superuser else ['admin'])
        if 'admin' not in roles:
            return Response(
                {'error': 'Accès réservé aux services internes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        etudiant  = get_object_or_404(Etudiant, pk=pk)
        matricule = request.data.get('matricule')
        if not matricule:
            return Response(
                {'error': 'Le matricule est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Etudiant.objects.filter(
            matricule=matricule
        ).exclude(pk=pk).exists():
            return Response(
                {'error': 'Ce matricule est déjà attribué.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        etudiant.matricule = matricule
        etudiant.save()
        tracer_action(
            request,
            action    = 'UPDATE',
            ressource = f'auth/etudiant/{pk}',
            details   = {'matricule': matricule}
        )
        return Response({
            'message'   : 'Matricule attribué avec succès.',
            'etudiant'  : etudiant.id,
            'matricule' : matricule,
        })


# ─────────────────────────────────────────────
#  RÔLES
# ─────────────────────────────────────────────

class RoleListView(APIView):
    """
    GET /api/auth/roles/  → liste tous les rôles
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        roles = Role.objects.all().order_by('libelle')
        return Response([
            {'id': r.id, 'libelle': r.libelle}
            for r in roles
        ])


# ─────────────────────────────────────────────
#  JOURNAL D'AUDIT
# ─────────────────────────────────────────────

class JournalAuditView(APIView):
    """
    GET /api/auth/audit/
    Consulter le journal d'audit.
    Réservé aux admins.
    """
    permission_classes = [IsAuthenticated, EstAdmin]

    def get(self, request):
        qs = JournalAudit.objects.all().order_by('-date_action')

        # Filtres
        action      = request.query_params.get('action')
        utilisateur = request.query_params.get('utilisateur_id')
        date_debut  = request.query_params.get('date_debut')
        date_fin    = request.query_params.get('date_fin')

        if action:
            qs = qs.filter(action=action)
        if utilisateur:
            qs = qs.filter(utilisateur_id=utilisateur)
        if date_debut:
            qs = qs.filter(date_action__date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date_action__date__lte=date_fin)

        # Pagination manuelle
        limit  = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        total  = qs.count()
        qs     = qs[offset:offset + limit]

        serializer = JournalAuditSerializer(qs, many=True)
        return Response({
            'count'  : total,
            'results': serializer.data,
        })


class EtudiantDetailView(RetrieveAPIView):
    queryset = Etudiant.objects.all()
    serializer_class = EtudiantSerializer


class EtudiantSearchView(APIView):
    """
    GET /api/auth/etudiants/search/?q=<terme>
    Recherche d'étudiants par nom, prénom ou username.
    Accessible aux agents et pédagogues (EstAgentOuAdmin).
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'results': []})

        qs = Utilisateur.objects.filter(
            roles__libelle='etudiant'
        ).filter(
            Q(username__icontains=q) |
            Q(etudiant__nom__icontains=q) |
            Q(etudiant__prenom__icontains=q)
        ).distinct()[:20]

        results = []
        for u in qs:
            try:
                nom_complet = u.etudiant.nom_complet
            except Exception:
                nom_complet = u.username
            results.append({
                'id'         : u.id,
                'username'   : u.username,
                'nom_complet': nom_complet,
            })
        return Response({'results': results})


class EtudiantNomsView(APIView):
    """
    GET /api/auth/etudiants/noms/?ids=1,2,3
    Retourne un dictionnaire {id: nom_complet} pour une liste d'IDs.
    Accessible aux agents et pédagogues (EstAgentOuAdmin).
    """
    permission_classes = [IsAuthenticated, EstAgentOuAdmin]

    def get(self, request):
        ids_param = request.query_params.get('ids', '')
        try:
            ids = [int(i) for i in ids_param.split(',') if i.strip()]
        except ValueError:
            return Response({'error': 'Paramètre ids invalide.'}, status=400)
        if not ids:
            return Response({})

        qs = Utilisateur.objects.filter(id__in=ids)
        result = {}
        for u in qs:
            try:
                result[u.id] = u.etudiant.nom_complet
            except Exception:
                result[u.id] = u.username
        return Response(result)
