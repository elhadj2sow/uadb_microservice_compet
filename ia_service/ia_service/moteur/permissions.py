from rest_framework.permissions import BasePermission


def get_roles(user):
    return getattr(user, 'roles', [])


class EstAdmin(BasePermission):
    message = 'Accès réservé aux administrateurs.'

    def has_permission(self, request, view):
        return 'admin' in get_roles(request.user)


class EstAgentOuAdmin(BasePermission):
    message = 'Accès réservé aux agents administratifs.'

    ROLES = {
        'agent_scolarite', 'agent_comptable',
        'service_medical', 'bibliotheque',
        'enseignant', 'responsable_pedagogique', 'admin'
    }

    def has_permission(self, request, view):
        return bool(self.ROLES.intersection(set(get_roles(request.user))))
