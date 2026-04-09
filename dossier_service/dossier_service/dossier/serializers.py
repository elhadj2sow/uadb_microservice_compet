from rest_framework import serializers
from django.conf import settings
from .models import (Formation, UniteEnseignement,
                     DossierEtudiant, PieceJustificative)


# ─────────────────────────────────────────────
#  FORMATION
# ─────────────────────────────────────────────

class UniteEnseignementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UniteEnseignement
        fields = [
            'id', 'code_ue', 'libelle_ue', 'semestre',
            'credit', 'coefficient', 'type_ue',
            'volume_horaire', 'actif'
        ]


class FormationSerializer(serializers.ModelSerializer):
    unites = UniteEnseignementSerializer(many=True, read_only=True)
    nb_ue  = serializers.SerializerMethodField()

    class Meta:
        model  = Formation
        fields = [
            'id', 'code_formation', 'libelle', 'niveau',
            'specialite', 'departement', 'credits_total',
            'duree_semestres', 'actif', 'nb_ue', 'unites'
        ]

    def get_nb_ue(self, obj):
        return obj.unites.filter(actif=True).count()


class FormationListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    nb_ue = serializers.SerializerMethodField()

    class Meta:
        model  = Formation
        fields = [
            'id', 'code_formation', 'libelle',
            'niveau', 'specialite', 'credits_total', 'actif', 'nb_ue'
        ]

    def get_nb_ue(self, obj):
        return obj.unites.filter(actif=True).count()


# ─────────────────────────────────────────────
#  PIÈCE JUSTIFICATIVE
# ─────────────────────────────────────────────

class PieceJustificativeSerializer(serializers.ModelSerializer):
    url_telechargement = serializers.SerializerMethodField()
    est_expiree        = serializers.SerializerMethodField()

    class Meta:
        model  = PieceJustificative
        fields = [
            'id', 'type_piece', 'nom_fichier',
            'taille_fichier', 'type_mime',
            'statut_verification', 'motif_rejet',
            'est_obligatoire', 'date_expiration',
            'date_depot', 'date_verification',
            'url_telechargement', 'est_expiree'
        ]
        read_only_fields = [
            'nom_fichier', 'taille_fichier', 'type_mime',
            'date_depot', 'date_verification', 'chemin_stockage'
        ]

    def get_url_telechargement(self, obj):
        """URL signée valable 5 minutes pour télécharger le fichier."""
        from .storage import generer_url_telechargement
        if obj.chemin_stockage:
            return generer_url_telechargement(obj.chemin_stockage)
        return None

    def get_est_expiree(self, obj):
        return obj.est_expiree


class DepotPieceSerializer(serializers.Serializer):
    """Serializer pour le dépôt d'une pièce justificative."""
    type_piece      = serializers.ChoiceField(
        choices=PieceJustificative.TYPE_CHOICES
    )
    fichier         = serializers.FileField()
    est_obligatoire = serializers.BooleanField(default=True)
    date_expiration = serializers.DateField(
        required=False, allow_null=True
    )

    def validate_fichier(self, fichier):
        # Vérifier la taille
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5242880)
        if fichier.size > max_size:
            raise serializers.ValidationError(
                f"Fichier trop volumineux. "
                f"Maximum autorisé : {max_size // 1024 // 1024} Mo."
            )
        # Vérifier le type MIME
        allowed = getattr(
            settings, 'ALLOWED_MIME_TYPES',
            ['application/pdf', 'image/jpeg', 'image/png']
        )
        if fichier.content_type not in allowed:
            raise serializers.ValidationError(
                f"Type de fichier non autorisé : {fichier.content_type}. "
                f"Types acceptés : PDF, JPEG, PNG."
            )
        return fichier


class VerifierPieceSerializer(serializers.Serializer):
    """Serializer pour la vérification d'une pièce par un agent."""
    action      = serializers.ChoiceField(
        choices=['valider', 'rejeter']
    )
    motif_rejet = serializers.CharField(
        required=False, allow_blank=True, default=''
    )

    def validate(self, data):
        if data['action'] == 'rejeter' and not data.get('motif_rejet'):
            raise serializers.ValidationError(
                {'motif_rejet': 'Le motif est obligatoire en cas de rejet.'}
            )
        return data


# ─────────────────────────────────────────────
#  DOSSIER ÉTUDIANT
# ─────────────────────────────────────────────

class DossierEtudiantSerializer(serializers.ModelSerializer):
    pieces          = PieceJustificativeSerializer(many=True, read_only=True)
    formation_detail = FormationListSerializer(
        source='formation', read_only=True
    )
    pieces_manquantes = serializers.SerializerMethodField()
    pieces_expirees   = serializers.SerializerMethodField()

    class Meta:
        model  = DossierEtudiant
        fields = [
            'id', 'etudiant_id', 'formation', 'formation_detail',
            'annee_universitaire', 'etat_dossier', 'score_completude',
            'date_creation', 'date_validation', 'observation',
            'valide_par', 'pieces', 'pieces_manquantes', 'pieces_expirees'
        ]
        read_only_fields = [
            'score_completude', 'etat_dossier',
            'date_creation', 'date_validation'
        ]

    def get_pieces_manquantes(self, obj):
        """Retourne la liste des types de pièces obligatoires manquantes."""
        from .signals import PIECES_OBLIGATOIRES
        types_deposes = set(
            obj.pieces.filter(
                statut_verification__in=('en_attente', 'valide')
            ).values_list('type_piece', flat=True)
        )
        manquantes = [
            t for t in PIECES_OBLIGATOIRES
            if t not in types_deposes
        ]
        return manquantes

    def get_pieces_expirees(self, obj):
        """Retourne la liste des pièces expirées."""
        from django.utils import timezone
        expirees = obj.pieces.filter(
            date_expiration__lt = timezone.now().date(),
            statut_verification = 'valide'
        ).values_list('type_piece', flat=True)
        return list(expirees)


class DossierListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes agents."""
    formation_libelle = serializers.CharField(
        source='formation.libelle', read_only=True
    )

    class Meta:
        model  = DossierEtudiant
        fields = [
            'id', 'etudiant_id', 'formation_libelle',
            'annee_universitaire', 'etat_dossier',
            'score_completude', 'date_creation'
        ]


class CreerDossierSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un dossier par l'étudiant."""
    class Meta:
        model  = DossierEtudiant
        fields = ['formation', 'annee_universitaire']

    def validate_annee_universitaire(self, value):
        import re
        if not re.match(r'^\d{4}-\d{4}$', value):
            raise serializers.ValidationError(
                "Format invalide. Utilisez : 2024-2025"
            )
        return value

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            return data
        etudiant_id = getattr(request.user, 'etudiant_id', None)
        if not etudiant_id:
            raise serializers.ValidationError(
                "Profil étudiant introuvable dans le token."
            )
        existe = DossierEtudiant.objects.filter(
            etudiant_id         = etudiant_id,
            annee_universitaire = data['annee_universitaire']
        ).exists()
        if existe:
            raise serializers.ValidationError(
                "Vous avez déjà un dossier pour cette année universitaire."
            )
        return data
