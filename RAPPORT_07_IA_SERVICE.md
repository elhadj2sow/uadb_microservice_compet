# Service Intelligence Artificielle — ia_service

## 1. Présentation

Le service IA est le **moteur de décision automatique** du système UADB. Il évalue des règles métier configurables en base de données et produit des décisions objectives sans intervention humaine. Il détecte également les **anomalies** et génère des alertes pour les administrateurs.

- **Port** : 8008
- **Préfixe URL** : `/api/ia/`
- **Base de données** : `uadb_ia` (schéma `moteur`)
- **Concept clé** : Règles stockées en base → modifiables sans redéployer le code

---

## 2. Modèles de Données

### 2.1 Modèle `RegleMetier`

Chaque règle est une condition Python évaluable associée à une action. Les règles sont stockées en base de données, ce qui permet de les modifier dynamiquement sans toucher au code.

| Champ | Type | Description |
|-------|------|-------------|
| `code_regle` | CharField(60) | Code unique ex. `DOSSIER_COMPLETUDE`, `DELIB_ADMISSION` |
| `libelle` | CharField(200) | Description lisible de la règle |
| `description` | TextField | Explication détaillée |
| `domaine` | CharField | `dossier`, `inscription`, `deliberation`, `attestation`, `workflow` |
| `condition` | TextField | Expression Python évaluable avec variables de contexte |
| `action` | CharField(50) | Résultat si la condition est vraie (ex. `eligible`, `admis`, `complet`) |
| `priorite` | IntegerField | Ordre d'évaluation (plus petit = évalué en premier) |
| `active` | BooleanField | Règle activée ou non |
| `date_creation` | DateTimeField | Création automatique |
| `date_maj` | DateTimeField | Dernière modification automatique |

**Exemple de règles en base** :

| Code | Condition | Action |
|------|-----------|--------|
| `DELIB_ADMIS` | `contexte['moyenne'] >= 10 and contexte['credits'] >= 60` | `admis` |
| `DELIB_RATTRAPAGE` | `contexte['moyenne'] >= 8 and contexte['moyenne'] < 10` | `rattrapage` |
| `DELIB_AJOURNE` | `contexte['moyenne'] < 8` | `ajourné` |
| `ATTEST_ELIGIBLE` | `contexte['inscription_validee'] == True and contexte['deliberation_cloturee'] == True` | `eligible` |
| `DOSSIER_COMPLET` | `contexte['score'] == 100` | `complet` |

---

### 2.2 Modèle `MoteurDecision`

Instance centrale (singleton) du moteur. Regroupe les règles actives.

| Champ | Type | Description |
|-------|------|-------------|
| `nom` | CharField | Nom du moteur (ex. `Moteur UADB v1`) |
| `version` | CharField | Version (ex. `1.0.0`) |
| `statut` | CharField | `actif` ou `inactif` |
| `regles` | ManyToManyField(RegleMetier) | Ensemble des règles associées |

---

### 2.3 Modèle `DecisionAutomatique`

Trace chaque décision prise par le moteur. Fournit la traçabilité complète.

| Champ | Type | Description |
|-------|------|-------------|
| `type_decision` | CharField | `completude_dossier`, `eligibilite_inscription`, `validation_deliberation`, `eligibilite_attestation`, `detection_anomalie` |
| `entite_id` | IntegerField | ID de l'entité concernée |
| `entite_type` | CharField | Type de l'entité (ex. `dossier`, `inscription`) |
| `contexte` | JSONField | Données d'entrée utilisées pour la décision |
| `regles_evaluees` | JSONField | Liste des règles évaluées avec leur résultat |
| `resultat` | CharField | Décision finale produite |
| `explication` | TextField | Justification lisible de la décision |
| `confiance` | DecimalField | Score de confiance (0 à 1) |
| `date_decision` | DateTimeField | Horodatage automatique |
| `service_demandeur` | CharField | Service qui a demandé la décision |

---

### 2.4 Modèle `AlerteAnomailie`

Alerte générée automatiquement quand une règle détecte une situation anormale.

| Champ | Type | Description |
|-------|------|-------------|
| `type_alerte` | CharField | `dossier_bloque`, `note_aberrante`, `doublon_inscription`, `delai_depasse` |
| `niveau_gravite` | CharField | `info`, `warning`, `critical` |
| `description` | TextField | Description de l'anomalie |
| `entite_id` | IntegerField | Entité concernée |
| `statut` | CharField | `ouverte`, `en_traitement`, `resolue` |
| `date_alerte` | DateTimeField | Date de détection automatique |
| `date_resolution` | DateTimeField | Date de résolution (nullable) |
| `resolue_par` | IntegerField | ID de l'administrateur qui a résolu |

---

## 3. Fonctionnement du Moteur

### 3.1 Algorithme d'Évaluation

```
ENTRÉE : type_decision + contexte (dictionnaire Python)

1. Charger les règles actives pour le domaine concerné
   (triées par priorité croissante)

2. Pour chaque règle :
   a. Évaluer la condition avec eval(règle.condition, {'contexte': contexte})
   b. Si condition == True → enregistrer (règle, action=règle.action)
   c. Si condition == False → passer à la règle suivante

3. La PREMIÈRE règle vraie (priorité la plus faible) détermine la décision

4. Enregistrer la DecisionAutomatique avec :
   - Toutes les règles évaluées
   - La décision finale
   - Le contexte d'entrée

SORTIE : décision + explication
```

### 3.2 Exemple d'Appel

**Requête d'un autre service** (ex. deliberation_service à la clôture) :

```json
POST /api/ia/evaluer/
{
  "type_decision": "validation_deliberation",
  "entite_id": 7,
  "entite_type": "resultat",
  "service_demandeur": "deliberation_service",
  "contexte": {
    "moyenne": 12.5,
    "credits": 60,
    "note_min": 8.0,
    "absences": 2
  }
}
```

**Réponse** :
```json
{
  "decision": "admis",
  "mention": "assez_bien",
  "explication": "Moyenne 12.5/20, crédits validés 60/60 — Admis en session normale",
  "confiance": 1.0,
  "regles_evaluees": [
    {"code": "DELIB_ADMIS", "resultat": true, "action": "admis"}
  ]
}
```

---

## 4. Endpoints de l'API

### 4.1 Endpoint Principal

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `POST` | `/api/ia/evaluer/` | Service interne | Soumettre un contexte pour décision |

### 4.2 Gestion des Règles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/ia/regles/` | Admin | Lister toutes les règles |
| `POST` | `/api/ia/regles/` | Admin | Créer une nouvelle règle |
| `GET/PATCH/DELETE` | `/api/ia/regles/{pk}/` | Admin | Modifier ou supprimer une règle |
| `POST` | `/api/ia/regles/{pk}/tester/` | Admin | Tester une règle avec un contexte de test |

### 4.3 Décisions et Alertes

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/ia/decisions/` | Admin | Historique de toutes les décisions |
| `GET` | `/api/ia/decisions/{pk}/` | Admin | Détail d'une décision avec contexte complet |
| `GET` | `/api/ia/alertes/` | Admin | Lister les alertes actives |
| `GET` | `/api/ia/alertes/{pk}/` | Admin | Détail d'une alerte |
| `POST` | `/api/ia/alertes/{pk}/resoudre/` | Admin | Marquer une alerte comme résolue |

### 4.4 Supervision

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/ia/moteur/statut/` | Admin | État du moteur (version, nb règles actives) |
| `GET` | `/api/ia/statistiques/` | Admin | Statistiques des décisions par type |

---

## 5. Services Consommateurs

| Service | Moment d'appel | Type de décision |
|---------|---------------|------------------|
| attestation_service | À la soumission d'une demande | `eligibilite_attestation` |
| deliberation_service | À la clôture d'une délibération | `validation_deliberation` |
| dossier_service | Quand une pièce est ajoutée | `completude_dossier` |
| inscription_service | À la réinscription | `eligibilite_inscription` |

---

## 6. Avantages du Moteur de Règles

| Avantage | Description |
|----------|-------------|
| **Sans redéploiement** | Modifier une règle en base suffit, sans toucher au code |
| **Traçabilité totale** | Chaque décision est enregistrée avec son contexte |
| **Explicabilité** | La décision est justifiée par des règles compréhensibles |
| **Testabilité** | Chaque règle peut être testée indépendamment via l'API |
| **Extensibilité** | Ajouter un nouveau domaine de règles sans modifier le moteur |
