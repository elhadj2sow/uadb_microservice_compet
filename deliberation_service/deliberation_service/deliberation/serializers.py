from rest_framework import serializers
from .models import Deliberation, Resultat, Note


# ─────────────────────────────────────────────
#  NOTE
# ─────────────────────────────────────────────

class NoteSerializer(serializers.ModelSerializer):
    valeur_calculee = serializers.SerializerMethodField()

    class Meta:
        model  = Note
        fields = [
            'id', 'ue_id', 'code_ue', 'libelle_ue',
            'credit_ue', 'coefficient_ue', 'semestre',
            'enseignant_id', 'note_cc', 'note_tp', 'note_examen',
            'valeur', 'valeur_calculee', 'est_validee',
            'est_rattrapable', 'note_rattrapage',
            'type_evaluation', 'date_saisie', 'verrouille'
        ]
        read_only_fields = ['valeur', 'est_validee', 'date_saisie']

    def get_valeur_calculee(self, obj):
        return obj.calculer_valeur()


class SaisirNoteSerializer(serializers.Serializer):
    """Saisie d'une note par un enseignant."""
    ue_id          = serializers.IntegerField()
    code_ue        = serializers.CharField(max_length=20, required=False, allow_blank=True)
    libelle_ue     = serializers.CharField(max_length=150, required=False, allow_blank=True)
    credit_ue      = serializers.IntegerField(default=3)
    coefficient_ue = serializers.DecimalField(
        max_digits=3, decimal_places=1, default=1.0
    )
    semestre       = serializers.IntegerField(default=1)
    note_cc        = serializers.DecimalField(
        max_digits=4, decimal_places=2,
        required=False, allow_null=True,
        min_value=0, max_value=20
    )
    note_tp        = serializers.DecimalField(
        max_digits=4, decimal_places=2,
        required=False, allow_null=True,
        min_value=0, max_value=20
    )
    note_examen    = serializers.DecimalField(
        max_digits=4, decimal_places=2,
        required=False, allow_null=True,
        min_value=0, max_value=20
    )
    note_rattrapage = serializers.DecimalField(
        max_digits=4, decimal_places=2,
        required=False, allow_null=True,
        min_value=0, max_value=20
    )
    type_evaluation = serializers.CharField(
        max_length=30, required=False, allow_blank=True
    )


class SaisirNotesBulkSerializer(serializers.Serializer):
    """Saisie de plusieurs notes en une seule requête."""
    etudiant_id = serializers.IntegerField()
    notes       = SaisirNoteSerializer(many=True)


# ─────────────────────────────────────────────
#  RÉSULTAT
# ─────────────────────────────────────────────

class ResultatSerializer(serializers.ModelSerializer):
    notes = NoteSerializer(many=True, read_only=True)
    progression = serializers.SerializerMethodField()

    class Meta:
        model  = Resultat
        fields = [
            'id', 'deliberation', 'etudiant_id', 'inscription_id',
            'moyenne_s1', 'moyenne_s2', 'moyenne_annuelle',
            'credits_valides', 'credits_total',
            'decision', 'mention', 'rang', 'observation',
            'valide_par', 'date_validation', 'date_creation',
            'progression', 'notes'
        ]
        read_only_fields = [
            'moyenne_annuelle', 'credits_valides',
            'decision', 'mention', 'date_creation'
        ]

    def get_progression(self, obj):
        total  = obj.notes.count()
        saisies = obj.notes.filter(valeur__isnull=False).count()
        if total == 0:
            return 0
        return round((saisies / total) * 100)


class ResultatListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes."""
    class Meta:
        model  = Resultat
        fields = [
            'id', 'etudiant_id', 'moyenne_annuelle',
            'credits_valides', 'decision', 'mention', 'rang'
        ]


class ValiderResultatSerializer(serializers.Serializer):
    """Validation de la décision par le jury."""
    decision    = serializers.ChoiceField(
        choices=['admis', 'rattrapage', 'ajourné', 'exclu']
    )
    mention     = serializers.ChoiceField(
        choices=['', 'passable', 'assez_bien', 'bien', 'tres_bien'],
        required=False, allow_blank=True, default=''
    )
    observation = serializers.CharField(
        required=False, allow_blank=True, default=''
    )
    rang        = serializers.IntegerField(required=False, allow_null=True)


# ─────────────────────────────────────────────
#  DÉLIBÉRATION
# ─────────────────────────────────────────────

class DeliberationSerializer(serializers.ModelSerializer):
    resultats     = ResultatListSerializer(many=True, read_only=True)
    nb_etudiants  = serializers.SerializerMethodField()
    nb_admis      = serializers.SerializerMethodField()
    taux_reussite = serializers.SerializerMethodField()

    class Meta:
        model  = Deliberation
        fields = [
            'id', 'session', 'annee_universitaire',
            'semestre', 'niveau', 'formation_id',
            'jury_president_id', 'date_deliberation',
            'date_creation', 'date_cloture', 'statut',
            'decision_finale', 'mention', 'observation',
            'nb_etudiants', 'nb_admis', 'taux_reussite',
            'resultats'
        ]

    def get_nb_etudiants(self, obj):
        return obj.resultats.count()

    def get_nb_admis(self, obj):
        return obj.resultats.filter(decision='admis').count()

    def get_taux_reussite(self, obj):
        total = obj.resultats.count()
        if total == 0:
            return 0
        admis = obj.resultats.filter(decision='admis').count()
        return round((admis / total) * 100, 1)


class DeliberationListSerializer(serializers.ModelSerializer):
    nb_etudiants = serializers.SerializerMethodField()

    class Meta:
        model  = Deliberation
        fields = [
            'id', 'session', 'annee_universitaire',
            'semestre', 'niveau', 'formation_id',
            'statut', 'date_deliberation', 'nb_etudiants'
        ]

    def get_nb_etudiants(self, obj):
        return obj.resultats.count()


class CreerDeliberationSerializer(serializers.ModelSerializer):
    class Meta:
        model      = Deliberation
        fields     = [
            'session', 'annee_universitaire', 'semestre',
            'niveau', 'formation_id', 'jury_president_id',
            'date_deliberation', 'observation'
        ]
        validators = []  # désactive UniqueTogetherValidator auto (géré dans validate())

    def validate_annee_universitaire(self, value):
        import re
        if not re.match(r'^\d{4}-\d{4}$', value):
            raise serializers.ValidationError(
                "Format invalide. Utilisez : 2024-2025"
            )
        return value

    def validate(self, data):
        existe = Deliberation.objects.filter(
            annee_universitaire = data['annee_universitaire'],
            semestre            = data['semestre'],
            formation_id        = data['formation_id'],
            session             = data['session'],
        ).exists()
        if existe:
            raise serializers.ValidationError(
                "Une délibération existe déjà pour cette "
                "formation, ce semestre et cette session."
            )
        return data


class CloturerDeliberationSerializer(serializers.Serializer):
    """Clôturer une délibération — verrouille toutes les notes."""
    decision_finale = serializers.CharField(
        required=False, allow_blank=True, default=''
    )
    observation     = serializers.CharField(
        required=False, allow_blank=True, default=''
    )
