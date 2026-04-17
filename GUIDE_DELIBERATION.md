# Guide complet — Système de Délibération UADB

> Ce document explique tout le fonctionnement du module délibération : qui fait quoi, dans quel ordre, et quelles règles s'appliquent.

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Les 3 objets principaux](#2-les-3-objets-principaux)
3. [Les rôles et permissions](#3-les-rôles-et-permissions)
4. [Le cycle de vie d'une délibération (étapes obligatoires)](#4-le-cycle-de-vie-dune-délibération)
5. [Calcul automatique des notes et moyennes](#5-calcul-automatique-des-notes-et-moyennes)
6. [Décisions possibles pour un étudiant](#6-décisions-possibles-pour-un-étudiant)
7. [Règles importantes à ne jamais oublier](#7-règles-importantes)
8. [Problèmes courants et solutions](#8-problèmes-courants-et-solutions)
9. [Lien entre formations et UEs](#9-lien-entre-formations-et-ues)
10. [Années universitaires](#10-années-universitaires)

---

## 1. Vue d'ensemble

Une **délibération** = une session d'évaluation d'une **formation** pour un **semestre** donné.

Exemple concret :
> "Délibération du Master 2 SI, Semestre 3, Session normale, Année 2027-2028"

Le service délibération tourne sur le **port 8004**.

---

## 2. Les 3 objets principaux

### 2.1 Délibération (`Deliberation`)

C'est le "conteneur" de la session. Il définit le cadre.

| Champ | Exemple | Explication |
|-------|---------|-------------|
| `session` | `normale` ou `rattrapage` | Type de session |
| `annee_universitaire` | `2027-2028` | Année saisie manuellement lors de la création |
| `semestre` | `1`, `2`, `3`, `4` | Numéro du semestre |
| `niveau` | `M2` | Niveau de la formation |
| `formation_id` | `3` | ID de la formation dans le **service dossier** (port 8003) |
| `statut` | voir section 4 | État actuel |
| `date_deliberation` | `2027-06-20` | Date prévue du jury |

> ⚠️ **La contrainte d'unicité** : il ne peut exister qu'UNE seule délibération pour la même combinaison `annee_universitaire + semestre + formation_id + session`. Essayer d'en créer une deuxième identique retourne une erreur.

---

### 2.2 Résultat (`Resultat`)

Un résultat = **une ligne par étudiant** dans la délibération.

| Champ | Explication |
|-------|-------------|
| `etudiant_id` | ID de l'étudiant dans le **service auth** (port 8001) |
| `inscription_id` | ID de l'inscription dans le **service inscription** (port 8002) — optionnel |
| `moyenne_annuelle` | Calculée automatiquement à chaque saisie de note |
| `credits_valides` | Crédits validés (calculés automatiquement) |
| `credits_total` | Total des crédits de l'année (60 par défaut) |
| `decision` | Décision du jury (voir section 6) |
| `mention` | Mention (Très Bien, Bien, etc.) |
| `rang` | Classement dans la délibération (calculé à la clôture) |

---

### 2.3 Note (`Note`)

Une note = **une ligne par UE (matière) par étudiant**.

| Champ | Explication |
|-------|-------------|
| `ue_id` | ID de l'UE dans le **service dossier** |
| `code_ue` | Code de la matière (ex: `M2S3-UE1`) |
| `libelle_ue` | Nom de la matière (ex: "Gouvernance des SI") |
| `note_cc` | Note de contrôle continu (0-20) |
| `note_tp` | Note de travaux pratiques (0-20) |
| `note_examen` | Note d'examen final (0-20) |
| `valeur` | Note finale calculée automatiquement |
| `verrouille` | `true` après clôture — **plus modifiable** |

---

## 3. Les rôles et permissions

| Action | Qui peut le faire |
|--------|-----------------|
| Créer une délibération | `responsable_pedagogique`, `admin` |
| Démarrer une délibération | `responsable_pedagogique`, `admin` |
| Ajouter un étudiant | `responsable_pedagogique`, `enseignant`, `admin` |
| Saisir des notes | `enseignant`, `responsable_pedagogique`, `admin` |
| Modifier la décision d'un étudiant | `responsable_pedagogique`, `enseignant`, `admin` |
| Clôturer une délibération | `responsable_pedagogique`, `admin` |
| Télécharger le PV PDF | `responsable_pedagogique`, `enseignant`, `admin` |
| Voir ses propres résultats | `etudiant` (uniquement les siens) |

---

## 4. Le cycle de vie d'une délibération

Une délibération passe obligatoirement par **3 statuts dans cet ordre** :

```
en_preparation  →  en_cours  →  cloturee
```

> ❌ **Impossible de sauter une étape** ou de revenir en arrière.

---

### Étape 1 : `en_preparation` (création)

**Qui** : Responsable pédagogique (menu Délibérations → + Nouvelle délibération)

**Ce qu'il faut remplir** :
- Session : `normale` ou `rattrapage`
- Année universitaire : ex `2026-2027` ← **attention à bien saisir l'année correcte**
- Semestre : 1, 2, 3 ou 4
- Niveau : L1, L2, L3, M1, M2
- Formation : choisir dans la liste
- Date de délibération : date prévue du jury

**À faire ensuite** : Ajouter les étudiants via le bouton 👤 (icône personnage).

**Règle** : On ne peut pas démarrer sans au moins 1 étudiant.

---

### Étape 2 : `en_cours` (démarrage)

**Qui** : Responsable pédagogique (bouton ▶ Démarrer)

**Ce que ça débloque** : Les enseignants peuvent maintenant saisir les notes.

**Règle** : Impossible de démarrer si la délibération a 0 étudiant.

---

### Étape 3 : Saisie des notes (pendant `en_cours`)

**Qui** : Enseignant (menu Saisie des notes)

**Comment ça marche** :
1. Sélectionner la délibération dans le menu déroulant
2. Cliquer sur l'étudiant dans la liste
3. Rechercher la matière (UE) dans le champ de recherche
4. Saisir CC, TP et/ou Examen
5. Cliquer Enregistrer

> La liste des matières vient automatiquement du **service dossier** selon la `formation_id` de la délibération.

---

### Étape 4 : `cloturee` (clôture)

**Qui** : Responsable pédagogique (menu ⌄ → Clôturer)

**Ce qui se passe automatiquement à la clôture** :
1. Le moteur de règles calcule automatiquement les décisions (`admis`, `rattrapage`, `ajourné`) pour tous les étudiants encore `en_attente`
2. Toutes les notes sont **verrouillées** (plus modifiables)
3. Les **rangs** sont calculés (classement par moyenne décroissante)
4. Chaque étudiant reçoit une **notification** avec sa décision et sa moyenne
5. Le **PV PDF** devient téléchargeable

---

## 5. Calcul automatique des notes et moyennes

### Note finale d'une UE

```
Note UE = CC × 30% + TP × 20% + Examen × 50%
```

Si seulement l'examen est saisi : `Note UE = Examen × 100%`

Si CC + Examen seulement : les poids sont normalisés proportionnellement.

> Ce calcul se fait **automatiquement** dès qu'une note est enregistrée.

---

### Moyenne annuelle de l'étudiant

La `moyenne_annuelle` est recalculée automatiquement à chaque saisie de note, en faisant la moyenne pondérée de toutes les notes UE de l'étudiant.

---

### Crédits validés

Une UE est **validée** si la note finale ≥ 10/20. Les crédits de cette UE sont alors ajoutés au compteur `credits_valides`.

---

## 6. Décisions possibles pour un étudiant

| Décision | Signification | Condition automatique typique |
|----------|--------------|-------------------------------|
| `en_attente` | Décision non encore rendue | État par défaut |
| `admis` | Admis en année supérieure | Moyenne ≥ 10 |
| `rattrapage` | Doit passer le rattrapage | Moyenne entre 8 et 10 |
| `ajourné` | Ajourné — doit redoubler | Moyenne < 8 |
| `exclu` | Exclusion académique | Cas exceptionnel |

**Mentions attribuées à la clôture** :

| Mention | Condition |
|---------|-----------|
| `Très Bien` | Moyenne ≥ 16 |
| `Bien` | Moyenne ≥ 14 |
| `Assez Bien` | Moyenne ≥ 12 |
| `Passable` | Moyenne ≥ 10 |
| *(aucune)* | Moyenne < 10 |

> Le responsable pédagogique peut **modifier manuellement** la décision d'un étudiant avant ou après la clôture (sur un résultat non verrouillé).

---

## 7. Règles importantes

### ⚠️ Règle 1 — L'année universitaire est saisie manuellement

Le formulaire de création ne propose pas d'année automatique. Si tu saisis `2027-2028` alors que tu voulais `2026-2027`, la délibération sera invisible dans la liste (car la liste filtre par année courante).

**Solution** : Utiliser le **sélecteur d'année** dans la barre de filtres pour voir les délibérations des autres années.

---

### ⚠️ Règle 2 — Les semestres M2 sont S3 et S4

| Niveau | Semestres |
|--------|-----------|
| L1 / M1 | S1 et S2 |
| L2 | S3 et S4 |
| L3 / M2 | S3 et S4 |

Les UEs du Master 2 Systèmes d'Information sont en **Semestre 3** (`M2S3-UE1`, etc.).  
Si tu crées une délibération M2 avec `semestre=1`, les UEs n'apparaissent pas dans le sélecteur de notes.

---

### ⚠️ Règle 3 — Unicité de la délibération

Il ne peut exister qu'une seule délibération pour :
```
formation + semestre + année universitaire + session
```

Si tu essaies d'en créer une deuxième identique, tu obtiens une erreur de validation.

---

### ⚠️ Règle 4 — L'enseignant ne voit que les délibérations `en_cours`

La page "Saisie des notes" ne montre **que** les délibérations avec `statut = en_cours`. Si la délibération est encore `en_preparation`, l'enseignant ne la verra pas.

**Solution** : Le responsable pédagogique doit cliquer **▶ Démarrer** avant que les enseignants puissent saisir des notes.

---

### ⚠️ Règle 5 — Après clôture : rien ne peut être modifié

Une fois clôturée, les notes sont verrouillées. Seul un admin peut modifier directement en base de données.

---

### ⚠️ Règle 6 — formation_id ≠ formation_id visible

La `formation_id` dans une délibération correspond à l'**ID dans la base du service dossier** (port 8003), pas à un numéro affiché.

Correspondance actuelle :
| ID | Formation |
|----|-----------|
| 1 | Licence 3 Informatique |
| 2 | Master 1 Systèmes d'Information |
| 3 | **Master 2 Systèmes d'Information** ← 16 UEs |
| 4 | Master 1 Systèmes et Réseaux |
| 5 | Master 2 Systèmes et Réseaux (0 UE pour l'instant) |

---

## 8. Problèmes courants et solutions

### "Aucune délibération en cours" dans Saisie des notes

**Cause** : La délibération est en `en_preparation` (pas encore démarrée).  
**Solution** : Le responsable pédagogique va dans Délibérations → clic sur ▶ **Démarrer**.

---

### "La délibération créée n'apparaît pas dans la liste"

**Cause** : L'année universitaire saisie ne correspond pas à l'année filtrée.  
**Solution** : Dans la page Délibérations, utiliser le **sélecteur d'année** (ex: choisir `2027-2028`) pour voir toutes les délibérations.

---

### "Aucune matière dans le champ de recherche"

**Causes possibles** :
1. La `formation_id` de la délibération est une formation qui n'a pas d'UEs (ex: formation id=5 a 0 UE)
2. Le service dossier (port 8003) n't est pas démarré

**Solution** : 
- Vérifier que le service dossier est actif
- Vérifier que la bonne formation a été choisie lors de la création

---

### "Cet étudiant est déjà dans cette délibération"

**Cause** : Tentative d'ajouter deux fois le même étudiant dans la même délibération.  
**Solution** : Normal, chaque étudiant n'a qu'une ligne par délibération. Cliquer sur l'étudiant existant pour saisir ses notes.

---

### "Impossible de saisir des notes après clôture"

**Cause** : La délibération est `cloturee`.  
**Solution** : Impossible. Toutes les notes sont verrouillées. Contacter l'admin.

---

## 9. Lien entre formations et UEs

Les **formations** et leurs **UEs (matières)** sont stockées dans le **service dossier** (port 8003).

Le service délibération communique avec le service dossier pour charger la liste des matières quand un enseignant saisit des notes.

```
Enseignant sélectionne délibération
    → Frontend appelle GET /api/formations/{formation_id}/ues/
    → Service dossier retourne la liste des UEs
    → L'enseignant voit la liste des matières
```

> Si le service dossier est éteint, le mode manuel s'active (champ "ID UE" à saisir manuellement).

---

## 10. Années universitaires

### Quelle année saisir ?

L'**année universitaire** correspond à l'année pendant laquelle se déroule la formation, pas l'année de début des cours.

Exemples :
- Cours commencés en octobre 2026, examens en juin 2027 → `2026-2027`
- Cours commencés en octobre 2027, examens en juin 2028 → `2027-2028`

### Format obligatoire

Toujours au format `AAAA-AAAA` avec un tiret :
- ✅ `2026-2027`
- ❌ `2026/2027`
- ❌ `2026`

### La liste ne montre que l'année courante par défaut

Le filtre par défaut affiche l'année calculée par le serveur : `année_actuelle - (année_actuelle + 1)`.  
En avril 2026, le filtre par défaut est `2026-2027`.

Pour voir d'autres années, utiliser le **sélecteur d'année** dans la barre de filtres de la page Délibérations.

---

## Résumé : checklist pour une délibération réussie

```
1. ☐ Responsable pédagogique crée la délibération
      - Choisir la BONNE année universitaire
      - Choisir le BON semestre (M2 = S3 ou S4)
      - Choisir la bonne formation

2. ☐ Responsable pédagogique ajoute les étudiants (bouton 👤)

3. ☐ Responsable pédagogique clique ▶ DÉMARRER
      (indispensable pour que les enseignants voient la délibération)

4. ☐ Enseignant(s) se connectent et saisissent les notes
      - Sélectionner la délibération dans le menu
      - Cliquer sur chaque étudiant
      - Rechercher la matière, saisir CC / TP / Examen
      - Enregistrer

5. ☐ Responsable pédagogique clique CLÔTURER
      - Les décisions sont calculées automatiquement
      - Les rangs sont attribués
      - Les étudiants reçoivent leurs résultats par notification
      - Le PV PDF est disponible
```
