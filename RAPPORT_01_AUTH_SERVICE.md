# Service d'Authentification — auth_service

## 1. Présentation

Le service d'authentification est le **point d'entrée central** du système UADB. Il gère l'identité de tous les utilisateurs (étudiants, agents, administrateurs) et émet les tokens JWT utilisés par l'ensemble des microservices pour sécuriser les accès.

- **Port** : 8001
- **Préfixe URL** : `/api/auth/`
- **Base de données** : `uadb_auth` (schéma `auth_uadb`)
- **Framework** : Django REST Framework + SimpleJWT

---

## 2. Modèles de Données

### 2.1 Modèle `Role`

Représente les rôles disponibles dans le système.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | Integer | Identifiant auto-incrémenté |
| `libelle` | CharField(50) | Nom unique du rôle |

**Rôles existants** : `etudiant`, `agent_scolarite`, `agent_comptable`, `service_medical`, `bibliotheque`, `pedagogique`, `admin`, `super_admin`

---

### 2.2 Modèle `Utilisateur`

Hérite de `AbstractUser` Django, qui fournit nativement :
- `username`, `password` (hashé bcrypt), `email`
- `first_name`, `last_name`
- `is_active`, `is_staff`, `date_joined`, `last_login`

Champs ajoutés :

| Champ | Type | Description |
|-------|------|-------------|
| `roles` | ManyToManyField(Role) | Rôles assignés à l'utilisateur |
| `etat_compte` | CharField | `actif`, `inactif`, `bloque`, `suspendu` |

**Propriétés calculées** :
- `role_list` → liste des libellés de rôles (inclus dans le token JWT)
- `est_etudiant` → vrai si le rôle `etudiant` est présent
- `est_admin` → vrai si le rôle `admin` est présent

---

### 2.3 Modèle `Etudiant`

Profil universitaire séparé des données d'authentification. Lié à `Utilisateur` par une relation `OneToOneField`.

| Champ | Type | Description |
|-------|------|-------------|
| `utilisateur` | OneToOneField(Utilisateur) | Lien vers le compte utilisateur |
| `matricule` | CharField(30) | Attribué par le service inscription après validation |
| `ine` | CharField(20) | Identifiant National Étudiant |
| `code_permanent` | CharField(20) | Code permanent unique |
| `nom` | CharField(100) | Nom de famille |
| `prenom` | CharField(100) | Prénom |
| `date_naissance` | DateField | Date de naissance |

---

### 2.4 Modèle `JournalAudit` (local)

Trace locale des connexions et des actions d'authentification, en complément du service audit centralisé.

---

## 3. Système d'Authentification JWT

Le service utilise **djangorestframework-simplejwt** avec un token personnalisé :

```
Payload du token JWT :
{
  "user_id": 42,
  "username": "diallo.mamadou",
  "email": "mamadou@uadb.edu.sn",
  "roles": ["etudiant"],
  "exp": 1746000000
}
```

- **Access token** : courte durée (ex. 60 minutes)
- **Refresh token** : longue durée (ex. 7 jours), blacklistable
- **Blacklist** : lors de la déconnexion, le refresh token est invalidé en base

---

## 4. Endpoints de l'API

### 4.1 Authentification

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `POST` | `/api/auth/login/` | Public | Connexion — retourne access + refresh token |
| `POST` | `/api/auth/logout/` | Authentifié | Déconnexion — blackliste le refresh token |
| `POST` | `/api/auth/refresh/` | Public | Renouvellement du token d'accès |
| `POST` | `/api/auth/register/` | Public | Création d'un compte étudiant |

**Exemple de requête POST /api/auth/login/ :**
```json
{
  "username": "diallo.mamadou",
  "password": "monMotDePasse"
}
```

**Exemple de réponse :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### 4.2 Profil Utilisateur Connecté

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/auth/me/` | Authentifié | Consulter son profil complet |
| `PATCH` | `/api/auth/me/` | Authentifié | Modifier son profil étudiant |
| `POST` | `/api/auth/change-password/` | Authentifié | Changer son mot de passe |

---

### 4.3 Gestion des Utilisateurs (Admin)

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/auth/utilisateurs/` | Admin | Lister tous les utilisateurs |
| `GET` | `/api/auth/utilisateurs/{pk}/` | Admin | Détail d'un utilisateur |
| `PATCH/DELETE` | `/api/auth/utilisateurs/{pk}/` | Admin | Modifier / Supprimer un utilisateur |
| `POST` | `/api/auth/utilisateurs/{pk}/roles/` | Admin | Assigner ou modifier les rôles |

---

### 4.4 Endpoints Internes (Inter-services)

| Méthode | URL | Description |
|---------|-----|-------------|
| `PATCH` | `/api/auth/etudiants/{pk}/matricule/` | Mis à jour du matricule après validation inscription |
| `GET` | `/api/auth/etudiants/{pk}/` | Récupérer les informations d'un étudiant |
| `GET` | `/api/auth/etudiants/search/` | Rechercher un étudiant par nom |
| `POST` | `/api/auth/etudiants/noms/` | Récupérer les noms en lot (batch) par liste d'IDs |

---

### 4.5 Autres Endpoints

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/auth/roles/` | Admin | Lister tous les rôles disponibles |
| `GET` | `/api/auth/audit/` | Admin | Consulter le journal d'audit local |

---

## 5. Permissions

| Classe Permission | Condition |
|-------------------|-----------|
| `EstAdmin` | `admin` dans les rôles |
| `EstEtudiant` | `etudiant` dans les rôles |
| `EstAgentOuAdmin` | `agent_scolarite` ou `admin` |

---

## 6. Traçabilité

Chaque action sensible est tracée via la fonction `tracer_action()` :
- Connexion réussie (`LOGIN`)
- Déconnexion (`LOGOUT`)
- Création de compte (`CREATE`)
- Mise à jour de profil (`UPDATE`)
- Changement de mot de passe (`RESET_PWD`)

Les traces sont envoyées à la fois dans le journal local et vers le **service audit centralisé** (audit_service :8009).

---

## 7. Sécurité

- Mots de passe **hashés avec bcrypt** via Django
- Tokens JWT **signés avec HS256** (clé secrète en variable d'environnement)
- Refresh token **blacklisté** à la déconnexion
- Variables sensibles stockées dans le fichier **`.env`** (non versionné)
- Protection CORS configurée pour le frontend uniquement
