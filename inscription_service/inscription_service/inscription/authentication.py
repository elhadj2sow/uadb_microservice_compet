from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed


class SimpleUser:
    """
    Objet utilisateur simplifié reconstruit depuis le token JWT.
    Évite un appel réseau vers le service auth à chaque requête.
    """
    def __init__(self, payload):
        self.id           = payload.get('user_id')
        self.username     = payload.get('login', '')
        self.email        = payload.get('email', '')
        self.roles        = payload.get('roles', [])
        self.etat         = payload.get('etat', 'actif')
        self.etudiant_id  = payload.get('etudiant_id')
        self.is_authenticated = True
        self.is_anonymous     = False

    def __str__(self):
        return self.username


class JWTFromAuthServiceAuthentication(JWTAuthentication):
    """
    Authentification JWT compatible avec les tokens émis
    par le service auth (contenant login, roles, etudiant_id).
    """

    def get_user(self, validated_token):
        try:
            return SimpleUser(validated_token)
        except Exception:
            raise AuthenticationFailed(
                'Token invalide ou utilisateur introuvable.'
            )
