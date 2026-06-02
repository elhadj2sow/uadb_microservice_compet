# Service Délibération — deliberation_service

## 1. Présentation

Le service délibération gère les sessions de jury, la saisie des notes et le calcul automatique des résultats académiques des étudiants. Il est le cœur du système pédagogique de l'UADB.

- **Port** : 8004
- **Préfixe URL** : `/api/`
- **Base de données** : `uadb_deliberation` (schéma `deliberation`)
- **Dépendances** : auth_service (JWT), dossier_service (formations + UEs), notification_service, audit_service

---

## 2. Modèles de Données

### 2.1 Modèle `Deliberation`

Représente une session de jury pour une formation donnée. Une délibération est unique par formation, année universitaire, semestre et session.

| Champ | Type | Description |
|-------|------|-------------|
| `session` | CharField | `normale` ou `rattrapage` |
| `annee_universitaire` | CharField | Ex. `2024-2025` |
| `semestre` | IntegerField | Numéro du semestre (1, 2, 3 ou 4) |
| `niveau` | CharField | `L1`, `L2`, `L3`, `M1`, `M2` |
| `formation_id` | IntegerField | ID de la formation dans dossier_service |
| `jury_president_id` | IntegerField | ID du président du jury dans auth_service |
| `date_deliberation` | DateField | Date prévue ou effective |
| `statut` | CharField | `en_preparation`, `en_cours`, `cloturee` |
| `decision_finale` | TextField | Résumé de la décision du jury |
| `mention` | CharField | Mention générale de la promotion |
| `observation` | TextField | Remarques du jury |
| `date_creation` | DateTimeField | Création automatique |
| `date_cloture` | DateTimeField | Clôture automatique |

**Contrainte** : `unique_together ('annee_universitaire', 'semestre', 'formation_id', 'session')`

---

### 2.2 Modèle `Resultat`

Une ligne par étudiant par délibération. Les moyennes sont calculées automatiquement via un signal Django déclenché à chaque saisie de note.

| Champ | Type | Description |
|-------|------|-------------|
| `deliberation` | ForeignKey(Deliberation) | Délibération parente |
| `etudiant_id` | IntegerField | ID de l'étudiant dans auth_service |
| `moyenne_s1` | DecimalField | Moyenne du semestre 1 |
| `moyenne_s2` | DecimalField | Moyenne du semestre 2 |
| `moyenne_annuelle` | DecimalField | Moyenne annuelle pondérée |
| `credits_valides` | IntegerField | Nombre de crédits obtenus |
| `decision` | CharField | `en_attente`, `admis`, `rattrapage`, `ajourné`, `exclu` |
| `mention` | CharField | `passable`, `assez_bien`, `bien`, `tres_bien` |
| `observation` | TextField | Observations sur l'étudiant |

**Règles de décision automatique** (via le moteur IA) :
| Condition | Décision |
|-----------|----------|
| Moyenne ≥ 10 et crédits ≥ seuil | `admis` |
| 8 ≤ Moyenne < 10 | `rattrapage` |
| Moyenne < 8 | `ajourné` |
| Cas particulier (fraude, abandon) | `exclu` |

---

### 2.3 Modèle `Note`

Détail de la note par Unité d'Enseignement pour un résultat donné.

| Champ | Type | Description |
|-------|------|-------------|
| `resultat` | ForeignKey(Resultat) | Résultat parent |
| `ue_id` | IntegerField | ID de l'UE dans dossier_service |
| `code_ue` | CharField | Code dénormalisé pour l'historique |
| `libelle_ue` | CharField | Libellé dénormalisé |
| `note_cc` | DecimalField | Note de contrôle continu (0–20) |
| `note_examen` | DecimalField | Note d'examen final (0–20) |
| `note_finale` | DecimalField | Note finale calculée |
| `credit` | IntegerField | Crédits de l'UE |
| `coefficient` | DecimalField | Coefficient de l'UE |
| `ue_validee` | BooleanField | Vrai si note ≥ 10 |
| `saisie_par` | IntegerField | ID de l'enseignant |
| `date_saisie` | DateTimeField | Date de saisie automatique |

**Calcul de la note finale** :
```
note_finale = (note_cc × 0.4) + (note_examen × 0.6)
```

---

## 3. Cycle de Vie d'une Délibération

```
1. CRÉATION      → statut = "en_preparation"
   ↓ (le jury est constitué, les résultats sont créés)
2. DÉMARRAGE     → statut = "en_cours"
   ↓ (saisie des notes par les enseignants)
3. SAISIE NOTES  → calcul automatique des moyennes et décisions
   ↓ (vérification par le président du jury)
4. CLÔTURE       → statut = "cloturee"
   ↓ (PV généré, notifications envoyées aux étudiants)
5. RÉSULTATS     → accessibles par les étudiants et l'inscription_service
```

---

## 4. Endpoints de l'API

### 4.1 Délibérations

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/deliberations/` | Pédagogue/Admin | Lister les délibérations |
| `POST` | `/api/deliberations/` | Admin | Créer une délibération |
| `GET` | `/api/deliberations/statistiques/` | Admin | Statistiques globales |
| `GET` | `/api/deliberations/{pk}/` | Pédagogue/Admin | Détail d'une délibération |
| `PATCH` | `/api/deliberations/{pk}/` | Admin | Modifier une délibération |
| `POST` | `/api/deliberations/{pk}/demarrer/` | Admin | Démarrer la session |
| `POST` | `/api/deliberations/{pk}/cloturer/` | Admin | Clôturer et calculer les décisions finales |
| `GET` | `/api/deliberations/{pk}/pv/` | Pédagogue/Admin | Générer le procès-verbal |

### 4.2 Résultats

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/deliberations/{pk}/resultats/` | Pédagogue/Admin | Lister les résultats d'une délibération |
| `GET` | `/api/resultats/mes-resultats/` | **Étudiant** | Consulter ses propres résultats |
| `GET` | `/api/resultats/{pk}/` | Pédagogue/Admin | Détail d'un résultat |
| `GET` | `/api/resultats/{pk}/notes/` | Pédagogue/Admin/Étudiant | Notes détaillées par UE |

### 4.3 Saisie des Notes

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `POST` | `/api/resultats/{pk}/notes/saisir/` | Pédagogue | Saisir une note unitaire |
| `POST` | `/api/resultats/notes/bulk/` | Pédagogue | Saisir plusieurs notes en une fois |

---

## 5. Calcul Automatique des Moyennes

Lorsqu'une note est enregistrée, un **signal Django `post_save`** se déclenche et recalcule automatiquement :

1. La **note finale** de chaque UE : `(CC × 0.4) + (Examen × 0.6)`
2. Les **crédits validés** : somme des crédits des UEs avec `note_finale ≥ 10`
3. La **moyenne semestrielle** : moyenne pondérée par les coefficients des UEs
4. La **moyenne annuelle** : `(moy_s1 + moy_s2) / 2`
5. La **décision** : calculée via le moteur de règles (ia_service)
6. La **mention** : calculée selon la moyenne annuelle

---

## 6. Utilisation par d'Autres Services

L'endpoint `GET /api/resultats/mes-resultats/` est consommé par :

- **inscription_service** : pour vérifier l'éligibilité à la réinscription
- **attestation_service** : pour générer les attestations de réussite, de passage et les relevés de notes

---

## 7. Procès-Verbal (PV)

À la clôture d'une délibération, le système génère un **procès-verbal** contenant :
- La liste de tous les étudiants avec leurs résultats
- Les décisions individuelles
- Les statistiques de réussite
- La signature du président du jury

---

## 8. Notifications à la Clôture

Quand une délibération est clôturée, **notification_service** envoie automatiquement à chaque étudiant :
- Sa **décision** (`admis`, `rattrapage`, etc.)
- Sa **mention** et sa **moyenne annuelle**
- Un lien pour consulter le détail de ses notes
