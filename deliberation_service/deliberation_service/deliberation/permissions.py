from rest_framework.permissions import BasePermission


def get_roles(user):
    return getattr(user, 'roles', [])


class EstEtudiant(BasePermission):
    message = 'Accès réservé aux étudiants.'

    def has_permission(self, request, view):
        return 'etudiant' in get_roles(request.user)


class EstEnseignant(BasePermission):
    message = 'Accès réservé aux enseignants.'

    def has_permission(self, request, view):
        roles = get_roles(request.user)
        return 'enseignant' in roles or 'admin' in roles


class EstResponsablePedagogique(BasePermission):
    message = 'Accès réservé aux responsables pédagogiques.'

    def has_permission(self, request, view):
        roles = get_roles(request.user)
        return (
            'responsable_pedagogique' in roles
            or 'admin' in roles
        )


class EstJuryOuAdmin(BasePermission):
    message = 'Accès réservé aux membres du jury.'

    ROLES_JURY = {
        'responsable_pedagogique',
        'enseignant',
        'admin'
    }

    def has_permission(self, request, view):
        roles = set(get_roles(request.user))
        return bool(self.ROLES_JURY.intersection(roles))


class EstAdmin(BasePermission):
    message = 'Accès réservé aux administrateurs.'

    def has_permission(self, request, view):
        return 'admin' in get_roles(request.user)
