from rest_framework.permissions import BasePermission


def get_roles(user):
    return getattr(user, 'roles', []) if hasattr(user, 'roles') else []


class EstAdmin(BasePermission):
    message = 'Accès réservé aux administrateurs.'

    def has_permission(self, request, view):
        if hasattr(request.user, 'role_list'):
            return 'admin' in request.user.role_list
        return request.user.is_superuser


class EstEtudiant(BasePermission):
    message = 'Accès réservé aux étudiants.'

    def has_permission(self, request, view):
        if hasattr(request.user, 'role_list'):
            return 'etudiant' in request.user.role_list
        return False


class EstAgentOuAdmin(BasePermission):
    message = 'Accès réservé aux agents administratifs.'

    ROLES_AGENTS = {
        'agent_scolarite', 'agent_comptable',
        'service_medical', 'bibliotheque',
        'enseignant', 'responsable_pedagogique', 'admin'
    }

    def has_permission(self, request, view):
        if hasattr(request.user, 'role_list'):
            return bool(
                self.ROLES_AGENTS.intersection(
                    set(request.user.role_list)
                )
            )
        return request.user.is_staff
