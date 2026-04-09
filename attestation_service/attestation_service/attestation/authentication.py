from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class SimpleUser:
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
    def get_user(self, validated_token):
        try:
            return SimpleUser(validated_token)
        except Exception:
            raise AuthenticationFailed('Token invalide.')
