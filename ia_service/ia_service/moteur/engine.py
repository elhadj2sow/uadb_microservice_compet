import logging
from .models import RegleMetier, DecisionAutomatique

logger = logging.getLogger(__name__)

# Fonctions Python autorisées dans les expressions de règles
NAMESPACE_SECURISE = {
    '__builtins__': {},
    'len'         : len,
    'sum'         : sum,
    'min'         : min,
    'max'         : max,
    'abs'         : abs,
    'round'       : round,
    'all'         : all,
    'any'         : any,
    'int'         : int,
    'float'       : float,
    'str'         : str,
    'bool'        : bool,
}


class MoteurRegles:
    """
    Implémentation du MoteurDecision du diagramme de classes.
    Charge les règles actives d'un domaine depuis la base,
    les évalue dans l'ordre de priorité,
    et retourne la première règle dont la condition est vraie.

    Méthodes du diagramme :
    - evaluerRegles()  → evaluer()
    - produireDecision() → tracer_decision()
    """

    def __init__(self, domaine: str):
        self.domaine = domaine
        self.regles  = RegleMetier.objects.filter(
            domaine=domaine,
            active=True
        ).order_by('priorite')

    def evaluer(self, contexte: dict) -> dict:
        """
        Évalue toutes les règles actives du domaine dans l'ordre.
        Retourne la première règle dont la condition est vraie.

        contexte : dict contenant les données à évaluer
        ex: {'score': 100}, {'moyenne': 13.5, 'credits': 60}
        """
        logger.info(
            f"Évaluation moteur domaine={self.domaine} "
            f"— {self.regles.count()} règle(s) active(s)"
        )

        for regle in self.regles:
            try:
                resultat = self._evaluer_condition(
                    regle.condition, contexte
                )
                if resultat:
                    logger.info(
                        f"Règle déclenchée : {regle.code_regle} "
                        f"→ {regle.action}"
                    )
                    return {
                        'resultat'        : regle.action,
                        'regle_appliquee' : regle,
                        'motif'           : regle.libelle,
                        'niveau_confiance': 1.0,
                    }
            except Exception as e:
                logger.warning(
                    f"Erreur évaluation règle {regle.code_regle} : {e}"
                )
                continue

        # Aucune règle ne correspond
        logger.info(f"Aucune règle applicable pour domaine={self.domaine}")
        return {
            'resultat'        : 'indetermine',
            'regle_appliquee' : None,
            'motif'           : 'Aucune règle applicable.',
            'niveau_confiance': 0.0,
        }

    def _evaluer_condition(self, condition: str, contexte: dict) -> bool:
        """
        Évalue une expression Python de manière sécurisée.
        Seules les fonctions du NAMESPACE_SECURISE sont disponibles.
        """
        ns = {**NAMESPACE_SECURISE, 'contexte': contexte}
        return bool(eval(condition, ns))

    def tracer_decision(
        self,
        type_decision: str,
        evaluation: dict,
        contexte: dict = None,
        **refs
    ) -> DecisionAutomatique:
        """
        Enregistre la décision en base pour traçabilité complète.
        Correspond à produireDecision() du diagramme.

        refs : etudiant_id, dossier_id, inscription_id,
               deliberation_id, demande_id
        """
        return DecisionAutomatique.objects.create(
            type_decision    = type_decision,
            resultat         = evaluation['resultat'],
            motif            = evaluation.get('motif', ''),
            niveau_confiance = evaluation.get('niveau_confiance', 1.0),
            regle_appliquee  = evaluation.get('regle_appliquee'),
            contexte_json    = contexte,
            etudiant_id      = refs.get('etudiant_id'),
            dossier_id       = refs.get('dossier_id'),
            inscription_id   = refs.get('inscription_id'),
            deliberation_id  = refs.get('deliberation_id'),
            demande_id       = refs.get('demande_id'),
        )
