# Microservice Authentification — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
auth_service/
├── .env                               ← variables d'environnement
├── requirements.txt                   ← dépendances Python
├── manage.py
├── init_db.sql                        ← script SQL d'initialisation PostgreSQL
├── auth_service/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── accounts/
    ├── __init__.py
    ├── models.py        ← Utilisateur, Etudiant, Role, JournalAudit
    ├── serializers.py   ← JWT personnalisé + validation
    ├── views.py         ← tous les endpoints REST
    ├── urls.py          ← routage complet
    ├── permissions.py   ← contrôle d'accès par rôle
    ├── utils.py         ← traçabilité JournalAudit
    ├── apps.py
    ├── admin.py         ← interface d'administration
    ├── migrations/
    │   └── 0001_initial.py  ← migration + création schéma + 8 rôles
    └── management/commands/
        └── init_schema.py   ← commande d'initialisation du schéma
```

---

## Installation et démarrage

### Étape 1 — Installer les dépendances

```bash
cd auth_service
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Étape 2 — Initialiser PostgreSQL

```bash
# En tant que superutilisateur PostgreSQL
psql -U postgres -f init_db.sql
```

### Étape 3 — Configurer les variables d'environnement

Éditer le fichier `.env` :

```
SECRET_KEY=changez-cette-cle-en-production
DEBUG=True
DB_NAME=uadb_db
DB_USER=uadb_user
DB_PASSWORD=uadb_pass
DB_HOST=localhost
DB_PORT=5432
```

### Étape 4 — Appliquer les migrations

```bash
# Créer le schéma PostgreSQL
python manage.py init_schema

# Appliquer les migrations Django
# (crée les tables + insère les 8 rôles automatiquement)
python manage.py migrate

# Créer/mettre à jour le compte interne utilisé par le service inscription
python manage.py init_internal_service_user
```

### Étape 5 — Créer un compte administrateur

```bash
python manage.py createsuperuser
```

### Étape 6 — Lancer le serveur
  python manage.py runserver 8001
```bash
# Service accessible sur : http://localhost:8001
```

---

## Endpoints disponibles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| POST | `/api/auth/login/` | Public | Connexion — retourne access + refresh token |
| POST | `/api/auth/logout/` | Connecté | Déconnexion — blackliste le refresh token |
| POST | `/api/auth/refresh/` | Public | Renouveler l'access token |
| POST | `/api/auth/register/` | Public | Créer un compte étudiant |
| GET | `/api/auth/me/` | Connecté | Profil de l'utilisateur connecté |
| PATCH | `/api/auth/me/` | Connecté | Modifier son profil |
| POST | `/api/auth/change-password/` | Connecté | Changer son mot de passe |
| GET | `/api/auth/utilisateurs/` | Admin | Lister tous les utilisateurs |
| GET | `/api/auth/utilisateurs/{id}/` | Admin | Détail d'un utilisateur |
| PATCH | `/api/auth/utilisateurs/{id}/` | Admin | Modifier etat_compte |
| POST | `/api/auth/utilisateurs/{id}/roles/` | Admin | Assigner/retirer un rôle |
| PATCH | `/api/auth/etudiants/{id}/matricule/` | Interne | MAJ matricule (service inscription) |
| GET | `/api/auth/roles/` | Admin | Lister les rôles |
| GET | `/api/auth/audit/` | Admin | Journal d'audit |

---

## Exemples d'appels API

### 1. Créer un compte étudiant

```bash
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username"        : "amadou.diallo",
    "email"           : "amadou@uadb.edu.sn",
    "password"        : "MonMotDePasse123",
    "password_confirm": "MonMotDePasse123",
    "nom"             : "Diallo",
    "prenom"          : "Amadou",
    "date_naissance"  : "2000-05-15",
    "sexe"            : "M",
    "telephone"       : "+221771234567"
  }'
```

**Réponse :**
```json
{
  "message" : "Compte créé avec succès.",
  "username": "amadou.diallo",
  "email"   : "amadou@uadb.edu.sn"
}
```

### 2. Connexion

```bash
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "amadou.diallo",
    "password": "MonMotDePasse123"
  }'
```

**Réponse :**
```json
{
  "access" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Token JWT décodé :**
```json
{
  "user_id"    : 1,
  "login"      : "amadou.diallo",
  "email"      : "amadou@uadb.edu.sn",
  "roles"      : ["etudiant"],
  "etat"       : "actif",
  "etudiant_id": 1,
  "exp"        : 1735689600
}
```

### 3. Consulter son profil

```bash
curl http://localhost:8001/api/auth/me/ \
  -H "Authorization: Bearer <access_token>"
```

### 4. Renouveler l'access token

```bash
curl -X POST http://localhost:8001/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

### 5. Assigner un rôle (admin)

```bash
curl -X POST http://localhost:8001/api/auth/utilisateurs/2/roles/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "role"  : "agent_scolarite",
    "action": "ajouter"
  }'
```

### 6. Bloquer un compte (admin)

```bash
curl -X PATCH http://localhost:8001/api/auth/utilisateurs/3/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{"etat_compte": "bloque"}'
```

---

## Les 8 rôles UADB

Créés automatiquement lors de la migration :

| Rôle | Description |
|------|-------------|
| `etudiant` | Étudiant — préinscription, consultation |
| `agent_scolarite` | Agent scolarité — validation dossiers |
| `agent_comptable` | Agent comptable — validation paiements |
| `service_medical` | Service médical — validation visite |
| `bibliotheque` | Bibliothèque — validation quitus |
| `enseignant` | Enseignant — saisie des notes |
| `responsable_pedagogique` | Responsable pédagogique — délibérations |
| `admin` | Administrateur — accès total |

---

## Structure du token JWT

Le token contient les données lues par tous les autres microservices :

```json
{
  "user_id"    : 42,
  "login"      : "amadou.diallo",
  "email"      : "amadou@uadb.edu.sn",
  "roles"      : ["etudiant"],
  "etat"       : "actif",
  "etudiant_id": 15,
  "exp"        : 1735689600,
  "iat"        : 1735687800
}
```

Les autres microservices (inscription, dossier, attestation...) lisent
`roles` et `etudiant_id` directement depuis le token — aucun appel
réseau vers le service auth n'est nécessaire.

---

## Tables PostgreSQL créées

| Table | Description |
|-------|-------------|
| `auth_uadb.utilisateur` | Comptes utilisateurs (hérite AbstractUser) |
| `auth_uadb.etudiant` | Profils universitaires étudiants |
| `auth_uadb.role` | 8 rôles UADB |
| `auth_uadb.utilisateur_role` | Table pivot ManyToMany |
| `auth_uadb.journal_audit` | Traçabilité de toutes les actions |
| `public.django_*` | Tables internes Django (sessions, permissions…) |
