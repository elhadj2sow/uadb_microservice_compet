import logging
import re
from difflib import SequenceMatcher

try:
    from nltk.classify import NaiveBayesClassifier
    from nltk.probability import DictionaryProbDist
    from nltk.stem.snowball import FrenchStemmer
    NLTK_AVAILABLE = True
except Exception:
    NaiveBayesClassifier = None
    DictionaryProbDist = None
    FrenchStemmer = None
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)

# ── Intentions et mots-clés ───────────────────────────────
INTENTIONS = {
    'inscription': [
        'inscription', 'inscrire', 'préinscription',
        'dossier inscription', 'comment s inscrire',
        'procédure inscription', 'inscris',
    ],
    'dossier': [
        'dossier', 'pièce', 'document', 'justificatif',
        'déposer', 'fichier', 'fournir',
    ],
    'deliberation': [
        'résultat', 'note', 'délibération', 'moyenne',
        'admis', 'ajourné', 'rattrapage', 'bulletin',
    ],
    'attestation': [
        'attestation', 'certificat', 'releve', 'document officiel',
        'télécharger', 'obtenir attestation',
    ],
    'paiement': [
        'paiement', 'frais', 'scolarité', 'orange money',
        'wave', 'payer', 'montant', 'reçu',
    ],
    'calendrier': [
        'calendrier', 'date', 'planning', 'rentrée',
        'examen', 'emploi du temps', 'délai',
    ],
    'contact': [
        'contact', 'téléphone', 'email', 'bureau',
        'scolarité', 'adresse', 'horaire',
    ],
    'salutation': [
        'bonjour', 'bonsoir', 'salut', 'hello',
        'bonne journée', 'merci',
    ],
    'aide': [
        'aide', 'aider', 'problème', 'question',
        'comment', 'que faire', 'que puis',
    ],
}

REPONSES_DEFAUT = {
    'salutation': (
        "Bonjour ! Je suis l'assistant virtuel de l'UADB. "
        "Je peux vous aider avec vos inscriptions, dossiers, "
        "résultats et attestations. Comment puis-je vous aider ?"
    ),
    'aide': (
        "Je suis disponible pour répondre à vos questions sur :\n"
        "• Les inscriptions et réinscriptions\n"
        "• La constitution de votre dossier\n"
        "• Vos résultats de délibération\n"
        "• Vos attestations et documents officiels\n"
        "• Les paiements et frais de scolarité\n\n"
        "Posez-moi votre question !"
    ),
    'defaut': (
        "Je n'ai pas bien compris votre question. "
        "Pouvez-vous la reformuler ? "
        "Vous pouvez aussi contacter directement la scolarité "
        "au +221 33 971 00 00 ou par email à scolarite@uadb.edu.sn."
    ),
}

# Stopwords FR minimales pour eviter les dependances externes (corpus NLTK).
STOPWORDS_FR = {
    'a', 'afin', 'ai', 'ainsi', 'alors', 'au', 'aucun', 'aussi', 'autre',
    'aux', 'avec', 'avoir', 'bon', 'car', 'ce', 'cela', 'ces', 'cet',
    'cette', 'comme', 'comment', 'dans', 'de', 'des', 'du', 'donc', 'elle',
    'elles', 'en', 'est', 'et', 'etre', 'fait', 'faire', 'faut', 'ici',
    'il', 'ils', 'je', 'la', 'le', 'les', 'leur', 'lui', 'ma', 'mais',
    'me', 'mes', 'mon', 'ne', 'nous', 'on', 'ou', 'par', 'pas', 'plus',
    'pour', 'puis', 'que', 'quel', 'quelle', 'quels', 'quelles', 'qui',
    'sa', 'se', 'ses', 'si', 'son', 'sur', 'ta', 'te', 'tes', 'toi', 'ton',
    'tu', 'un', 'une', 'vos', 'votre', 'vous', 'y'
}

PIECES_DOSSIER_HINTS = {
    'piece', 'pieces', 'document', 'documents', 'justificatif',
    'justificatifs', 'fournir'
}


class MoteurChatbot:
    """
    Moteur de chatbot basé sur la BaseConnaissance.
    Utilise la similarité de texte pour trouver la meilleure réponse.
    Correspond à la classe Chatbot du diagramme de classes.
    """

    def __init__(self):
        self.seuil_confiance = 0.45
        self.seuil_intention_ml = 0.50
        self.stemmer = FrenchStemmer() if NLTK_AVAILABLE else None
        self.classifier = self._build_classifier() if NLTK_AVAILABLE else None
        self.pieces_hint_tokens = set()
        for hint in PIECES_DOSSIER_HINTS:
            self.pieces_hint_tokens.update(self._normaliser_tokens(hint))

        self.pieces_specific_tokens = set()
        for hint in ('piece', 'pieces', 'document', 'documents', 'justificatif', 'justificatifs', 'fournir'):
            self.pieces_specific_tokens.update(self._normaliser_tokens(hint))

    def traiter_message(self, texte_utilisateur, contexte=None):
        """
        Traite un message de l'étudiant et retourne une réponse.

        Retourne dict :
        {
            'reponse'   : str,
            'intention' : str,
            'confiance' : float,
            'source'    : 'base_connaissance' | 'defaut' | 'salutation',
        }
        """
        contexte = contexte or {}
        texte_nettoye = self._nettoyer(texte_utilisateur)
        if isinstance(contexte, dict):
            dernier_sujet = self._nettoyer(str(contexte.get('dernier_sujet', '')))
            if dernier_sujet:
                texte_nettoye = f"{texte_nettoye} {dernier_sujet}".strip()

        # 1. Détecter les salutations
        intention_salut = self._detecter_salutation(texte_nettoye)
        if intention_salut:
            return {
                'reponse'  : REPONSES_DEFAUT['salutation'],
                'intention': 'salutation',
                'confiance': 1.0,
                'source'   : 'salutation',
            }

        # 2. Chercher dans la BaseConnaissance
        resultat_bc = self._chercher_base_connaissance(texte_nettoye)
        if resultat_bc:
            return resultat_bc

        # 3. Detecter l'intention generale (ML + fallback regles)
        intention, confiance = self._detecter_intention_ml(texte_nettoye)
        if not intention:
            intention = self._detecter_intention(texte_nettoye)
            confiance = 0.45 if intention else 0.0

        # 4. Réponse selon l'intention
        if intention == 'aide':
            return {
                'reponse'  : REPONSES_DEFAUT['aide'],
                'intention': 'aide',
                'confiance': round(max(confiance, 0.8), 2),
                'source'   : 'defaut',
            }

        # 5. Réponse par défaut
        return {
            'reponse'  : REPONSES_DEFAUT['defaut'],
            'intention': intention or 'inconnu',
            'confiance': round(confiance, 2),
            'source'   : 'defaut',
        }

    def _nettoyer(self, texte):
        """Nettoie et normalise le texte."""
        texte = texte.lower().strip()
        # Supprimer les caractères spéciaux
        texte = re.sub(r'[^\w\s\'-]', ' ', texte)
        # Normaliser les espaces
        texte = re.sub(r'\s+', ' ', texte)
        return texte

    def _detecter_salutation(self, texte):
        """Détecte si le message est une salutation."""
        mots_salut = INTENTIONS.get('salutation', [])
        for mot in mots_salut:
            if mot in texte:
                return True
        return False

    def _detecter_intention(self, texte):
        """Détecte l'intention principale du message."""
        scores = {}
        texte_stems = set(self._normaliser_tokens(texte))

        for intention, mots_cles in INTENTIONS.items():
            score = 0
            for mot in mots_cles:
                mot_nettoye = self._nettoyer(mot)
                mot_stems = set(self._normaliser_tokens(mot_nettoye))

                match_direct = mot_nettoye in texte
                match_stem = bool(mot_stems and mot_stems.intersection(texte_stems))
                if match_direct or match_stem:
                    score += 1
            if score > 0:
                scores[intention] = score

        if not scores:
            return None
        return max(scores, key=scores.get)

    def _normaliser_tokens(self, texte):
        """Tokenise, filtre les mots vides et applique un stemming FR."""
        tokens = re.findall(r"[a-z0-9']+", self._nettoyer(texte))
        tokens = [t for t in tokens if len(t) > 1 and t not in STOPWORDS_FR]
        if self.stemmer:
            return [self.stemmer.stem(t) for t in tokens]
        return tokens

    def _build_classifier(self):
        """Construit un petit classifieur d'intentions base sur les exemples metier."""
        train_set = []

        for intention, expressions in INTENTIONS.items():
            for expression in expressions:
                train_set.append((self._features_from_text(expression), intention))
                train_set.append((self._features_from_text(f"Je veux {expression}"), intention))
                train_set.append((self._features_from_text(f"Aidez-moi pour {expression}"), intention))

        if not train_set:
            return None

        try:
            return NaiveBayesClassifier.train(train_set)
        except Exception as exc:
            logger.warning("Classification NLTK desactivee: %s", exc)
            return None

    def _features_from_text(self, texte):
        """Features lexicales robustes pour la classification d'intention."""
        tokens = self._normaliser_tokens(texte)
        token_set = set(tokens)
        features = {
            'len_tokens': min(len(tokens), 12),
            'has_question': '?' in texte,
            'contains_annee': bool(re.search(r'\b\d{4}-\d{4}\b', texte)),
        }

        for intention, expressions in INTENTIONS.items():
            stems = set()
            for exp in expressions:
                stems.update(self._normaliser_tokens(exp))
            features[f'hit_{intention}'] = bool(token_set.intersection(stems))

        for token in list(token_set)[:20]:
            features[f'w={token}'] = True

        return features

    def _detecter_intention_ml(self, texte):
        """Detecte l'intention via NLTK et retourne (intention, confiance)."""
        if not self.classifier or not NLTK_AVAILABLE:
            return None, 0.0

        try:
            feats = self._features_from_text(texte)
            dist = self.classifier.prob_classify(feats)
            intention = dist.max()
            confiance = dist.prob(intention)
            if confiance < self.seuil_intention_ml:
                return None, confiance
            return intention, confiance
        except Exception as exc:
            logger.warning("Erreur classification NLTK: %s", exc)
            return None, 0.0

    def _chercher_base_connaissance(self, texte):
        """
        Cherche la meilleure réponse dans la BaseConnaissance.
        Utilise la similarité de séquence et les mots-clés.
        """
        from .models import BaseConnaissance

        entrees = BaseConnaissance.objects.filter(actif=True)
        meilleur_score = 0
        meilleure_entree = None

        texte_tokens = set(self._normaliser_tokens(texte))
        focus_pieces = bool(texte_tokens.intersection(self.pieces_specific_tokens))

        for entree in entrees:
            score = self._calculer_score(texte, entree)

            # Heuristique metier: si la question porte sur les pieces,
            # prioriser les entrees qui traitent explicitement des documents.
            if focus_pieces:
                entree_tokens = set(self._normaliser_tokens(
                    " ".join([
                        entree.titre,
                        entree.questions,
                        entree.mots_cles,
                        entree.categorie,
                    ])
                ))
                if entree_tokens.intersection(self.pieces_specific_tokens):
                    score += 0.20
                elif entree.categorie == 'dossier':
                    score -= 0.10

            # Legere priorisation de la connaissance admin (priorite plus faible = meilleure)
            score += max(0.0, (10 - min(entree.priorite, 10))) * 0.005

            if score > meilleur_score:
                meilleur_score = score
                meilleure_entree = entree

        if meilleure_entree and meilleur_score >= self.seuil_confiance:
            return {
                'reponse'  : meilleure_entree.contenu,
                'intention': meilleure_entree.categorie,
                'confiance': round(min(1.0, meilleur_score), 2),
                'source'   : 'base_connaissance',
            }
        return None

    def _calculer_score(self, texte, entree):
        """
        Calcule le score de pertinence d'une entrée
        pour le texte donné.
        Combine similarité avec les questions
        et présence de mots-clés.
        """
        score_max = 0
        texte_tokens = set(self._normaliser_tokens(texte))

        # Similarité avec les questions déclencheurs
        for question in entree.liste_questions:
            q_nettoyee = self._nettoyer(question)
            sim = SequenceMatcher(
                None, texte, q_nettoyee
            ).ratio()
            score_max = max(score_max, sim)

            # Bonus si les mots clés sont présents
            mots_q = set(self._normaliser_tokens(q_nettoyee))
            intersection = mots_q.intersection(texte_tokens)
            if intersection:
                bonus = len(intersection) / max(len(mots_q), 1)
                score_max = max(score_max, bonus * 0.7)

        # Bonus pour les mots-clés de l'entrée
        for mot_cle in entree.liste_mots_cles:
            mot_nettoye = self._nettoyer(mot_cle)
            if mot_nettoye in texte:
                score_max = max(score_max, 0.6)
                continue

            mot_tokens = set(self._normaliser_tokens(mot_nettoye))
            if mot_tokens and mot_tokens.intersection(texte_tokens):
                score_max = max(score_max, 0.6)

        return score_max
