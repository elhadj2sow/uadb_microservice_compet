from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Utilisateur, Etudiant, Role, JournalAudit


class CustomTokenSerializer(TokenObtainPairSerializer):
    """
    Surcharge du serializer JWT pour injecter les données UADB
    dans le token. Tous les microservices lisent ces données
    sans appel réseau vers le service auth.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Données injectées dans le payload JWT
        token['login']  = user.username
        token['email']  = user.email
        token['roles']  = user.role_list
        token['etat']   = user.etat_compte

        # ID du profil étudiant (None si pas étudiant)
        try:
            token['etudiant_id'] = user.etudiant.id
        except Exception:
            token['etudiant_id'] = None

        return token

    def validate(self, attrs):
        # Si l'identifiant ressemble à un email, on cherche le username correspondant
        identifiant = attrs.get('username', '')
        if '@' in identifiant:
            try:
                user_obj = Utilisateur.objects.get(email__iexact=identifiant)
                attrs['username'] = user_obj.username
            except Utilisateur.DoesNotExist:
                raise serializers.ValidationError(
                    'Aucun compte trouvé avec cette adresse email.'
                )

        # Vérifier que le compte n'est pas bloqué
        data = super().validate(attrs)
        user = self.user
        if user.etat_compte in ('bloque', 'suspendu', 'inactif'):
            raise serializers.ValidationError(
                f"Compte {user.etat_compte}. "
                f"Contactez l'administration."
            )
        return data


class EtudiantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Etudiant
        fields = [
            'id', 'matricule', 'ine', 'code_permanent',
            'nom', 'prenom', 'date_naissance', 'lieu_naissance',
            'sexe', 'telephone', 'statut'
        ]
        read_only_fields = ['matricule']


class UtilisateurSerializer(serializers.ModelSerializer):
    roles    = serializers.StringRelatedField(many=True, read_only=True)
    etudiant = EtudiantSerializer(read_only=True)

    class Meta:
        model  = Utilisateur
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'etat_compte', 'date_joined', 'last_login',
            'roles', 'etudiant'
        ]
        read_only_fields = ['date_joined', 'last_login']


class RegisterEtudiantSerializer(serializers.Serializer):
    """
    Création d'un compte étudiant complet.
    Crée Utilisateur + Etudiant + assigne le rôle 'etudiant'.
    """
    # Données d'authentification
    username = serializers.CharField(max_length=150)
    email    = serializers.EmailField()
    password = serializers.CharField(
        write_only = True,
        min_length = 8,
        style      = {'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only = True,
        style      = {'input_type': 'password'}
    )

    # Données du profil étudiant
    nom            = serializers.CharField(max_length=100)
    prenom         = serializers.CharField(max_length=100)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    lieu_naissance = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    sexe      = serializers.ChoiceField(
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        required=False, allow_blank=True
    )
    telephone = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    ine = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )

    def validate_username(self, value):
        if Utilisateur.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà pris."
            )
        return value

    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Cette adresse email est déjà utilisée."
            )
        return value.lower()

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': 'Les mots de passe ne correspondent pas.'}
            )
        try:
            validate_password(data['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return data

    def create(self, validated_data):
        from django.db import transaction

        # Extraire les données du profil étudiant
        nom            = validated_data.pop('nom')
        prenom         = validated_data.pop('prenom')
        date_naissance = validated_data.pop('date_naissance', None)
        lieu_naissance = validated_data.pop('lieu_naissance', '')
        sexe           = validated_data.pop('sexe', '')
        telephone      = validated_data.pop('telephone', '')
        ine            = validated_data.pop('ine', None)

        with transaction.atomic():
            # Créer le compte utilisateur
            user = Utilisateur.objects.create_user(
                username = validated_data['username'],
                email    = validated_data['email'],
                password = validated_data['password'],
            )

            # Assigner le rôle étudiant
            role_etudiant, _ = Role.objects.get_or_create(libelle='etudiant')
            user.roles.add(role_etudiant)

            # Créer le profil étudiant
            Etudiant.objects.create(
                utilisateur    = user,
                nom            = nom,
                prenom         = prenom,
                date_naissance = date_naissance,
                lieu_naissance = lieu_naissance,
                sexe           = sexe,
                telephone      = telephone,
                ine            = ine if ine else None,
            )

        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe par l'utilisateur connecté."""
    ancien_password  = serializers.CharField(write_only=True)
    nouveau_password = serializers.CharField(
        write_only=True, min_length=8
    )
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['nouveau_password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'Les mots de passe ne correspondent pas.'}
            )
        try:
            validate_password(data['nouveau_password'])
        except ValidationError as e:
            raise serializers.ValidationError(
                {'nouveau_password': list(e.messages)}
            )
        return data


class UpdateProfilSerializer(serializers.ModelSerializer):
    """Mise à jour du profil étudiant par l'utilisateur connecté."""
    class Meta:
        model  = Etudiant
        fields = [
            'nom', 'prenom', 'date_naissance',
            'lieu_naissance', 'sexe', 'telephone'
        ]


class JournalAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model  = JournalAudit
        fields = [
            'id', 'date_action', 'action', 'ressource',
            'acteur', 'adresse_ip', 'details'
        ]


class UtilisateurListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    roles    = serializers.StringRelatedField(many=True, read_only=True)
    nom_complet = serializers.SerializerMethodField()
    etudiant_id = serializers.SerializerMethodField()

    class Meta:
        model  = Utilisateur
        fields = [
            'id', 'username', 'email', 'nom_complet',
            'etat_compte', 'roles', 'etudiant_id', 'date_joined'
        ]

    def get_nom_complet(self, obj):
        try:
            return obj.etudiant.nom_complet
        except Exception:
            return f"{obj.first_name} {obj.last_name}".strip()

    def get_etudiant_id(self, obj):
        try:
            return obj.etudiant.id
        except Exception:
            return None


class AssignerRoleSerializer(serializers.Serializer):
    """Assigner ou retirer un rôle à un utilisateur (admin)."""
    role    = serializers.CharField(max_length=50)
    action  = serializers.ChoiceField(
        choices=['ajouter', 'retirer'],
        default='ajouter'
    )
