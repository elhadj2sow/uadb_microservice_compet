# Service d'Inscription — inscription_service

## 1. Présentation

Le service d'inscription gère l'ensemble du processus d'inscription administrative des étudiants à l'UADB. Il couvre la préinscription, le workflow de validation multi-étapes, le paiement des frais, et la réinscription avec contrôle de la politique académique.

- **Port** : 8002
- **Préfixe URL** : `/api/`
- **Base de données** : `uadb_inscription` (schéma `inscription`)
- **Dépendances** : auth_service (JWT + profil étudiant), dossier_service (formations), deliberation_service (résultats pour réinscription), notification_service (emails), audit_service (traçabilité)

---

## 2. Modèles de Données

### 2.1 Modèle `Inscription`

Table centrale du service. Une inscription unique par étudiant et par année universitaire.

| Champ | Type | Description |
|-------|------|-------------|
| `etudiant_id` | IntegerField | ID de l'étudiant dans auth_service |
| `formation_id` | IntegerField | ID de la formation dans dossier_service |
| `dossier_id` | IntegerField | ID du dossier dans dossier_service |
| `annee_universitaire` | CharField | Ex. : `2024-2025` |
| `type_inscription` | CharField | `premiere` ou `reinscription` |
| `statut_inscription` | CharField | `en_attente`, `en_cours`, `validee`, `rejetee`, `annulee` |
| `numero_provisoire` | CharField | Attribué à la préinscription (UUID court) |
| `numero_matricule` | CharField | Attribué après validation complète |
| `date_preinscription` | DateTimeField | Date de soumission automatique |
| `date_inscription` | DateTimeField | Date de validation définitive |
| `valide_par` | IntegerField | ID de l'agent validateur |
| `observation` | TextField | Remarques libres |

**Contrainte** : `unique_together ('etudiant_id', 'annee_universitaire')` — un étudiant ne peut s'inscrire qu'une fois par année.

---

### 2.2 Modèle `Paiement`

Lié à une inscription par une relation `OneToOneField`.

| Champ | Type | Description |
|-------|------|-------------|
| `inscription` | OneToOneField(Inscription) | Inscription concernée |
| `montant_total` | DecimalField | Montant dû selon le niveau |
| `montant_verse` | DecimalField | Montant effectivement payé |
| `mode_paiement` | CharField | `especes`, `virement`, `orange_money`, `wave`, `cheque`, `paytech` |
| `statut_paiement` | CharField | `en_attente`, `partiel`, `confirme`, `rembourse` |
| `reference_paiement` | CharField | Référence unique de transaction |
| `date_paiement` | DateTimeField | Date du paiement |
| `valide_par` | IntegerField | ID de l'agent comptable |

**Frais d'inscription par niveau** :
- L1, L2, L3 : **25 000 FCFA**
- M1, M2 : **50 000 FCFA**

---

### 2.3 Modèle `ValidationService`

Représente la validation d'une étape du workflow par un service.

| Champ | Type | Description |
|-------|------|-------------|
| `inscription` | ForeignKey(Inscription) | Inscription concernée |
| `service` | CharField | `scolarite`, `comptabilite`, `medical`, `bibliotheque` |
| `statut` | CharField | `en_attente`, `valide`, `rejete` |
| `valide_par` | IntegerField | ID de l'agent |
| `date_validation` | DateTimeField | Date de validation |
| `commentaire` | TextField | Observations de l'agent |

---

### 2.4 Modèles `EmpruntLivre` et `PenaliteBibliotheque`

Gèrent la situation bibliothécaire de l'étudiant (emprunts en cours, amendes impayées), consultée lors du workflow de validation.

---

## 3. Workflow d'Inscription

Le processus d'inscription est structuré en **4 étapes de validation** :

```
ÉTUDIANT          SCOLARITÉ       COMPTABILITÉ      MÉDICAL        BIBLIOTHÈQUE
    │                 │                │               │                │
    ├─ Préinscription ─►              │               │                │
    │  (numéro provisoire)            │               │                │
    │                 │               │               │                │
    │            ◄─── Validation ─────│               │                │
    │            (dossier complet ?)  │               │                │
    │                 │               │               │                │
    │                 ├── Notification paiement ──────►                │
    │                 │               │               │                │
    │                 │          ◄─── Validation paiement             │
    │                 │               │               │                │
    │                 │               │  ◄── Visite médicale ─────────►
    │                 │               │               │                │
    │                 │               │               │   ◄── Situation bibliothèque ─►
    │                 │               │               │                │
    ▼ INSCRIPTION VALIDÉE — Attribution du matricule définitif
```

---

## 4. Politique de Réinscription

Avant toute réinscription, le service consulte les résultats de l'année précédente via le **deliberation_service** :

| Décision de l'année précédente | Réinscription |
|---------------------------------|---------------|
| `admis` | Autorisée normalement |
| `rattrapage` | Autorisée avec message d'information |
| `ajourné` | **Bloquée** — étudiant doit régulariser |
| `exclu` | **Bloquée** — étudiant exclu |

---

## 5. Intégration PayTech

Le service supporte le paiement en ligne via **PayTech** (passerelle de paiement sénégalaise) :

1. `POST /inscriptions/{pk}/paiement/paytech/initier/` → Génère une URL de paiement
2. L'étudiant est redirigé vers la page de paiement PayTech
3. Après paiement, PayTech appelle le webhook : `POST /inscriptions/paiement/paytech/webhook/`
4. Le service met à jour le statut du paiement automatiquement

---

## 6. Endpoints de l'API

### 6.1 Côté Étudiant

| Méthode | URL | Description |
|---------|-----|-------------|
| `POST` | `/api/inscriptions/` | Soumettre une préinscription |
| `GET` | `/api/inscriptions/mon-inscription/` | Consulter sa dernière inscription |
| `GET` | `/api/inscriptions/mes-inscriptions/` | Historique de toutes ses inscriptions |
| `GET` | `/api/inscriptions/reinscription/eligibilite/` | Vérifier son éligibilité à la réinscription |
| `POST` | `/api/inscriptions/reinscription/` | Soumettre une réinscription |
| `GET` | `/api/inscriptions/{pk}/workflow/` | Suivre l'avancement du workflow |
| `GET/POST` | `/api/inscriptions/{pk}/paiement/` | Consulter ou soumettre un paiement |
| `POST` | `/api/inscriptions/{pk}/paiement/paytech/initier/` | Initier un paiement PayTech |

### 6.2 Côté Agents / Administration

| Méthode | URL | Description |
|---------|-----|-------------|
| `GET` | `/api/inscriptions/liste/` | Lister toutes les inscriptions (filtrables) |
| `GET` | `/api/inscriptions/statistiques/` | Statistiques d'inscription |
| `GET/PATCH` | `/api/inscriptions/{pk}/` | Détail et modification d'une inscription |
| `POST` | `/api/inscriptions/{pk}/valider-etape/` | Valider ou rejeter une étape du workflow |
| `GET` | `/api/inscriptions/bibliotheque/situation/` | Situation bibliothécaire d'un étudiant |
| `GET` | `/api/inscriptions/bibliotheque/emprunts/` | Lister les emprunts |
| `GET/PATCH` | `/api/inscriptions/bibliotheque/emprunts/{pk}/` | Détail et retour d'emprunt |
| `GET` | `/api/inscriptions/bibliotheque/penalites/` | Lister les pénalités |
| `PATCH` | `/api/inscriptions/bibliotheque/penalites/{pk}/` | Marquer une pénalité payée |

---

## 7. Notifications Automatiques

À chaque changement d'étape, le service envoie une notification via **notification_service** :

| Événement | Type |
|-----------|------|
| Préinscription reçue | Email de confirmation avec numéro provisoire |
| Étape validée | Email d'avancement du dossier |
| Étape rejetée | Email avec motif du rejet |
| Inscription définitivement validée | Email avec matricule définitif |
| Paiement confirmé | Email de reçu de paiement |

---

## 8. Traçabilité

Toutes les actions sont enregistrées dans le service audit :
- Soumission de préinscription (`SUBMIT`)
- Validation d'une étape (`VALIDATE`)
- Rejet d'une étape (`REJECT`)
- Confirmation de paiement (`VALIDATE`)
