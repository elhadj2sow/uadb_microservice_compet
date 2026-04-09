from rest_framework.permissions import BasePermission


def get_roles(user):
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


class EstAgentOuAdmin(BasePermission):
    message = 'Accès réservé aux agents administratifs.'

    ROLES_AGENTS = {
        'agent_scolarite', 'agent_comptable',
        'service_medical', 'bibliotheque',
        'responsable_pedagogique', 'admin'
    }

    def has_permission(self, request, view):
        roles = set(get_roles(request.user))
        return bool(self.ROLES_AGENTS.intersection(roles))


class EstAdmin(BasePermission):
    message = 'Accès réservé aux administrateurs.'

    def has_permission(self, request, view):
        return 'admin' in get_roles(request.user)
