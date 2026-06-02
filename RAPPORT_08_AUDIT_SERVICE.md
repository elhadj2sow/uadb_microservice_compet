# Service Audit — audit_service

## 1. Présentation

Le service audit est le **journal centralisé de toutes les actions** effectuées dans le système UADB. Chaque microservice y envoie une trace à chaque opération sensible. Il fournit une vue complète de qui a fait quoi, quand et depuis quel service.

- **Port** : 8009
- **Préfixe URL** : `/api/`
- **Base de données** : `uadb_audit` (schéma `audit`)
- **Mode de fonctionnement** : Réception passive — tous les services l'appellent

---

## 2. Modèle de Données

### 2.1 Modèle `JournalAudit`

Table unique centrale de tous les événements du système.

#### Qui a effectué l'action

| Champ | Type | Description |
|-------|------|-------------|
| `utilisateur_id` | IntegerField | ID utilisateur dans auth_service (NULL si action système) |
| `acteur` | CharField(150) | Username dénormalisé pour la lisibilité de l'historique |
| `role_acteur` | CharField(50) | Rôle de l'acteur au moment de l'action |

#### Quelle action

| Champ | Type | Description |
|-------|------|-------------|
| `action` | CharField | Code de l'action effectuée (voir liste ci-dessous) |
| `niveau` | CharField | `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `statut` | CharField | `succes`, `echec`, `partiel` |
| `description` | TextField | Description lisible de l'action effectuée |

#### Sur quelle ressource

| Champ | Type | Description |
|-------|------|-------------|
| `service` | CharField | Microservice source : `auth`, `inscription`, `dossier`, `deliberation`, `attestation`, `ia`, `notification` |
| `ressource` | CharField | Chemin de la ressource concernée (ex. `inscription/42`) |
| `ressource_id` | IntegerField | ID numérique de la ressource |

#### Contexte technique

| Champ | Type | Description |
|-------|------|-------------|
| `adresse_ip` | GenericIPAddressField | IP du client |
| `user_agent` | CharField | Navigateur ou client HTTP |
| `methode_http` | CharField | `GET`, `POST`, `PATCH`, `DELETE` |
| `url` | CharField | URL complète de la requête |
| `details` | JSONField | Données supplémentaires libres (contexte métier) |
| `date_action` | DateTimeField | Horodatage automatique de l'action |

---

### 2.2 Actions Disponibles

#### Authentification
| Code | Description |
|------|-------------|
| `LOGIN` | Connexion réussie |
| `LOGOUT` | Déconnexion |
| `LOGIN_ECHEC` | Tentative de connexion échouée |
| `RESET_PWD` | Réinitialisation de mot de passe |

#### Gestion des Données
| Code | Description |
|------|-------------|
| `CREATE` | Création d'un enregistrement |
| `UPDATE` | Modification d'un enregistrement |
| `DELETE` | Suppression d'un enregistrement |
| `READ` | Consultation (lecture sensible) |

#### Processus Métier
| Code | Description |
|------|-------------|
| `VALIDATE` | Validation (inscription, pièce, paiement...) |
| `REJECT` | Rejet (inscription, pièce...) |
| `SUBMIT` | Soumission (préinscription, demande) |
| `CANCEL` | Annulation |

#### Documents
| Code | Description |
|------|-------------|
| `UPLOAD` | Dépôt de fichier |
| `DOWNLOAD` | Téléchargement de document |
| `GENERATE` | Génération de document (PDF) |
| `VERIFY` | Vérification d'authenticité |

#### Automatisation
| Code | Description |
|------|-------------|
| `DECISION_AUTO` | Décision automatique par le moteur IA |
| `ALERTE` | Détection d'anomalie |
| `WORKFLOW_START` | Démarrage d'un workflow |
| `WORKFLOW_STEP` | Avancement d'une étape de workflow |
| `WORKFLOW_END` | Fin d'un workflow |

#### Administration
| Code | Description |
|------|-------------|
| `EXPORT` | Export de données |
| `IMPORT` | Import de données |
| `CONFIG` | Modification de configuration système |

---

### 2.3 Modèle `StatistiqueAudit`

Agrégats calculés périodiquement pour les tableaux de bord administratifs.

| Champ | Type | Description |
|-------|------|-------------|
| `date` | DateField | Jour concerné |
| `service` | CharField | Microservice |
| `action` | CharField | Type d'action |
| `nb_succes` | IntegerField | Nombre d'actions réussies |
| `nb_echec` | IntegerField | Nombre d'actions échouées |
| `nb_total` | IntegerField | Total des actions |

---

## 3. Endpoints de l'API

### 3.1 Traçage (appelé par tous les microservices)

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `POST` | `/api/audit/tracer/` | Service interne | Enregistrer une nouvelle action |

**Exemple de corps de requête (envoyé par inscription_service)** :
```json
{
  "utilisateur_id": 42,
  "acteur": "agent.scolarite",
  "role_acteur": "agent_scolarite",
  "action": "VALIDATE",
  "niveau": "INFO",
  "statut": "succes",
  "description": "Validation de l'étape scolarité pour l'inscription #15",
  "service": "inscription",
  "ressource": "inscriptions/15",
  "ressource_id": 15,
  "methode_http": "POST",
  "details": {
    "etape": "scolarite",
    "etudiant_id": 7,
    "annee": "2024-2025"
  }
}
```

### 3.2 Consultation du Journal

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/audit/journal/` | Admin | Lister toutes les entrées (paginées, filtrables) |
| `GET` | `/api/audit/journal/{pk}/` | Admin | Détail complet d'une entrée |
| `GET` | `/api/audit/etudiants/{etudiant_id}/journal/` | Admin | Journal d'un étudiant spécifique |
| `GET` | `/api/audit/utilisateurs/{utilisateur_id}/journal/` | Admin | Journal d'un utilisateur spécifique |

**Filtres disponibles sur `/api/audit/journal/`** :
- `service` : filtrer par microservice
- `action` : filtrer par type d'action
- `niveau` : filtrer par niveau (`INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- `statut` : filtrer par résultat (`succes`, `echec`, `partiel`)
- `date_debut` / `date_fin` : filtrer par période
- `utilisateur_id` : filtrer par acteur

### 3.3 Statistiques

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/audit/statistiques/` | Admin | Statistiques globales (nb actions, taux d'échec) |
| `GET` | `/api/audit/statistiques/daily/` | Admin | Statistiques jour par jour |
| `POST` | `/api/audit/statistiques/calculer/` | Admin | Recalculer les agrégats manuellement |

### 3.4 Maintenance

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `DELETE` | `/api/audit/purger/` | Super Admin | Purger les entrées plus anciennes qu'une période |
| `GET` | `/api/audit/meta/` | Authentifié | Liste des actions et niveaux disponibles (pour les formulaires React) |

---

## 4. Qui Alimente le Service Audit

| Service | Actions tracées |
|---------|----------------|
| **auth_service** | LOGIN, LOGOUT, LOGIN_ECHEC, CREATE utilisateur, UPDATE profil, RESET_PWD, ASSIGNER_ROLE |
| **inscription_service** | SUBMIT préinscription, VALIDATE étape, REJECT étape, VALIDATE paiement, WORKFLOW_START, WORKFLOW_END |
| **dossier_service** | UPLOAD pièce, VERIFY pièce (valide/rejete), CREATE dossier, VALIDATE dossier |
| **deliberation_service** | CREATE délibération, WORKFLOW_START, SAISIR note (SUBMIT), CLOTURER (WORKFLOW_END) |
| **attestation_service** | SUBMIT demande, DECISION_AUTO, GENERATE PDF, DOWNLOAD, VERIFY |
| **ia_service** | DECISION_AUTO, ALERTE |
| **notification_service** | Échecs d'envoi (ERROR) |

---

## 5. Cas d'Usage

### 5.1 Vérification d'Intégrité
Un administrateur peut consulter le journal pour vérifier qu'un agent a bien validé une inscription, avec l'heure exacte et l'IP de connexion.

### 5.2 Détection d'Intrusion
En filtrant sur `action=LOGIN_ECHEC` et `niveau=WARNING`, on peut détecter des tentatives de connexion suspectes (brute force).

### 5.3 Traçabilité Réglementaire
Pour chaque attestation délivrée, le journal contient l'ensemble de la chaîne : soumission, décision IA, génération, téléchargements successifs.

### 5.4 Support et Débogage
En cas de réclamation d'un étudiant, l'équipe support peut reconstituer tout l'historique de son dossier en filtrant sur son `etudiant_id`.

---

## 6. Sécurité du Journal

- Le journal est en **écriture seule** depuis les services applicatifs (endpoint `POST /api/audit/tracer/`)
- La **suppression** (purge) est réservée au rôle `super_admin` et requiert une confirmation
- Toutes les requêtes de consultation du journal sont elles-mêmes **tracées** (READ)
- Le journal peut être exporté pour archivage externe (action `EXPORT`)
