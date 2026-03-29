from rest_framework.permissions import BasePermission


def get_roles(user):
    """Récupère les rôles depuis le token JWT décodé."""
    return getattr(user, 'roles', [])


class EstEtudiant(BasePermission):
    message = 'Accès réservé aux étudiants.'

    def has_permission(self, request, view):
        return 'etudiant' in get_roles(request.user)


class EstAgentScolarite(BasePermission):
    message = 'Accès réservé aux agents de scolarité.'

    def has_permission(self, request, view):
        roles = get_roles(request.user)
        return 'agent_scolarite' in roles or 'admin' in roles


class EstAgentComptable(BasePermission):
    message = 'Accès réservé aux agents comptables.'

    def has_permission(self, request, view):
        roles = get_roles(request.user)
        return 'agent_comptable' in roles or 'admin' in roles


class EstServiceMedical(BasePermission):
    message = 'Accès réservé au service médical.'

    def has_permission(self, request, view):
        roles = get_roles(request.user)
        return 'service_medical' in roles or 'admin' in roles


class EstBibliotheque(BasePermission):
    message = 'Accès réservé à la bibliothèque.'

    def has_permission(self, request, view):
        roles = get_roles(request.user)
        return 'bibliotheque' in roles or 'admin' in roles


class EstAgentOuAdmin(BasePermission):
    """Tout agent administratif ou admin."""
    message = 'Accès réservé aux agents administratifs.'

    def has_permission(self, request, view):
        roles = get_roles(request.user)
        agents = {
            'agent_scolarite', 'agent_comptable',
            'service_medical', 'bibliotheque', 'admin'
        }
        return bool(agents.intersection(set(roles)))


class EstAdmin(BasePermission):
    message = 'Accès réservé aux administrateurs.'

    def has_permission(self, request, view):
        return 'admin' in get_roles(request.user)
