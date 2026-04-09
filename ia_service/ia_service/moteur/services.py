import logging
from django.conf import settings
import requests

from .engine import MoteurRegles
from .models import AlerteAnomalie

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  SERVICE DOSSIER
# ─────────────────────────────────────────────

class ServiceDossier:
    """Règles métier pour la complétude des dossiers étudiants."""

    def evaluer_completude(
        self, dossier_id: int, score: int, etudiant_id: int
    ) -> dict:
        moteur   = MoteurRegles(domaine='dossier')
        contexte = {'score_completude': score, 'score': score}
        evaluation = moteur.evaluer(contexte)

        decision = moteur.tracer_decision(
            type_decision = 'completude_dossier',
            evaluation    = evaluation,
            contexte      = contexte,
            etudiant_id   = etudiant_id,
            dossier_id    = dossier_id,
        )

        # Alerte si dossier très incomplet
        if score < 30:
            AlerteAnomalie.objects.get_or_create(
                type_alerte        = 'dossier_incomplet',
                dossier_id         = dossier_id,
                statut_traitement  = 'ouverte',
                defaults={
                    'niveau_gravite': 'moyenne',
                    'description'   : (
                        f"Dossier {dossier_id} — étudiant {etudiant_id} : "
                        f"score {score}% — très incomplet."
                    ),
                    'etudiant_id': etudiant_id,
                }
            )

        return {
            'eligible'   : evaluation['resultat'] == 'complet',
            'resultat'   : evaluation['resultat'],
            'motif'      : evaluation['motif'],
            'confiance'  : evaluation['niveau_confiance'],
            'decision_id': decision.id,
        }


# ─────────────────────────────────────────────
#  SERVICE DÉLIBÉRATION
# ─────────────────────────────────────────────

class ServiceDeliberation:
    """Règles métier pour la validation académique des délibérations."""

    def evaluer_resultat(
        self,
        moyenne: float,
        credits: int,
        etudiant_id: int,
        deliberation_id: int
    ) -> dict:
        moteur   = MoteurRegles(domaine='deliberation')
        contexte = {
            'moyenne' : float(moyenne),
            'credits' : int(credits),
        }
        evaluation = moteur.evaluer(contexte)

        # Calculer la mention séparément
        mention = self._calculer_mention(float(moyenne))

        decision = moteur.tracer_decision(
            type_decision   = 'validation_deliberation',
            evaluation      = evaluation,
            contexte        = contexte,
            etudiant_id     = etudiant_id,
            deliberation_id = deliberation_id,
        )

        # Alerte si note aberrante
        if float(moyenne) > 20 or float(moyenne) < 0:
            AlerteAnomalie.objects.create(
                type_alerte     = 'note_aberrante',
                niveau_gravite  = 'elevee',
                description     = (
                    f"Moyenne aberrante détectée : {moyenne}/20 "
                    f"pour l'étudiant {etudiant_id}, "
                    f"délibération {deliberation_id}."
                ),
                etudiant_id     = etudiant_id,
                deliberation_id = deliberation_id,
            )

        return {
            'decision'   : evaluation['resultat'],
            'mention'    : mention,
            'motif'      : evaluation['motif'],
            'confiance'  : evaluation['niveau_confiance'],
            'decision_id': decision.id,
        }

    def _calculer_mention(self, moyenne: float) -> str:
        if moyenne >= 16:
            return 'tres_bien'
        if moyenne >= 14:
            return 'bien'
        if moyenne >= 12:
            return 'assez_bien'
        if moyenne >= 10:
            return 'passable'
        return ''


# ─────────────────────────────────────────────
#  SERVICE ATTESTATION
# ─────────────────────────────────────────────

class ServiceAttestation:
    """Règles métier pour l'éligibilité aux attestations."""

    def verifier_eligibilite(
        self,
        etudiant_id: int,
        type_att: str,
        inscription_validee: bool,
        decision: str = ''
    ) -> dict:
        moteur   = MoteurRegles(domaine='attestation')
        contexte = {
            'inscription_validee': inscription_validee,
            'type_att'           : type_att,
            'decision'           : decision,
        }
        evaluation = moteur.evaluer(contexte)

        decision_obj = moteur.tracer_decision(
            type_decision = 'eligibilite_attestation',
            evaluation    = evaluation,
            contexte      = contexte,
            etudiant_id   = etudiant_id,
        )

        return {
            'eligible'   : evaluation['resultat'] == 'eligible',
            'resultat'   : evaluation['resultat'],
            'motif'      : evaluation['motif'],
            'confiance'  : evaluation['niveau_confiance'],
            'decision_id': decision_obj.id,
        }


# ─────────────────────────────────────────────
#  SERVICE INSCRIPTION
# ─────────────────────────────────────────────

class ServiceInscription:
    """Règles métier pour l'éligibilité à l'inscription."""

    def verifier_eligibilite(
        self,
        etudiant_id: int,
        score_dossier: int,
        paiement_confirme: bool,
        dossier_id: int = None
    ) -> dict:
        moteur   = MoteurRegles(domaine='inscription')
        contexte = {
            'score_dossier'    : score_dossier,
            'paiement_confirme': paiement_confirme,
        }
        evaluation = moteur.evaluer(contexte)

        decision = moteur.tracer_decision(
            type_decision = 'eligibilite_inscription',
            evaluation    = evaluation,
            contexte      = contexte,
            etudiant_id   = etudiant_id,
            dossier_id    = dossier_id,
        )

        return {
            'eligible'   : evaluation['resultat'] == 'eligible',
            'resultat'   : evaluation['resultat'],
            'motif'      : evaluation['motif'],
            'confiance'  : evaluation['niveau_confiance'],
            'decision_id': decision.id,
        }


# ─────────────────────────────────────────────
#  DISPATCHER PRINCIPAL
# ─────────────────────────────────────────────

SERVICES = {
    'completude_dossier'     : ServiceDossier,
    'validation_deliberation': ServiceDeliberation,
    'eligibilite_attestation': ServiceAttestation,
    'eligibilite_inscription': ServiceInscription,
}


def dispatcher(type_evaluation: str, data: dict) -> dict:
    """
    Dispatch vers le bon service métier selon le type d'évaluation.
    Point d'entrée unique appelé par la vue EvaluerView.
    """
    if type_evaluation not in SERVICES:
        return {
            'error': f"Type d'évaluation inconnu : {type_evaluation}",
            'types_valides': list(SERVICES.keys()),
        }

    ServiceClass = SERVICES[type_evaluation]
    service      = ServiceClass()

    try:
        if type_evaluation == 'completude_dossier':
            return service.evaluer_completude(
                dossier_id  = data.get('dossier_id', 0),
                score       = data.get('score', 0),
                etudiant_id = data.get('etudiant', 0),
            )
        elif type_evaluation == 'validation_deliberation':
            return service.evaluer_resultat(
                moyenne         = data.get('moyenne', 0),
                credits         = data.get('credits', 0),
                etudiant_id     = data.get('etudiant', 0),
                deliberation_id = data.get('deliberation_id', 0),
            )
        elif type_evaluation == 'eligibilite_attestation':
            return service.verifier_eligibilite(
                etudiant_id         = data.get('etudiant', 0),
                type_att            = data.get('type_att', ''),
                inscription_validee = data.get('inscription_validee', False),
                decision            = data.get('decision', ''),
            )
        elif type_evaluation == 'eligibilite_inscription':
            return service.verifier_eligibilite(
                etudiant_id       = data.get('etudiant', 0),
                score_dossier     = data.get('score_dossier', 0),
                paiement_confirme = data.get('paiement_confirme', False),
                dossier_id        = data.get('dossier_id'),
            )
    except Exception as e:
        logger.error(f"Erreur dispatcher type={type_evaluation} : {e}")
        return {'error': str(e)}
