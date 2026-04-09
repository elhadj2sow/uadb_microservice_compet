# Microservice Inscription — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
inscription_service/
├── .env                          ← variables d'environnement
├── requirements.txt              ← dépendances Python
├── manage.py
├── init_db.sql                   ← script SQL d'initialisation PostgreSQL
├── inscription_service/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── inscription/
    ├── models.py                 ← Inscription, Paiement, ValidationService,
    │                                Workflow, EtapeWorkflow
    ├── serializers.py            ← sérialisation DRF
    ├── views.py                  ← endpoints REST par acteur
    ├── urls.py                   ← routage
    ├── signals.py                ← moteur workflow automatique
    ├── permissions.py            ← contrôle d'accès par rôle
    ├── authentication.py         ← JWT inter-services
    ├── apps.py                   ← connexion des signaux
    ├── admin.py                  ← interface d'administration
    ├── migrations/
    │   └── 0001_initial.py       ← migration initiale
    └── management/commands/
        └── init_schema.py        ← commande d'initialisation du schéma
```

---

## Installation et démarrage

### Étape 1 — Cloner et installer les dépendances

```bash
cd inscription_service
python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

### Étape 2 — Configurer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL en tant que superutilisateur
psql -U postgres

# Exécuter le script d'initialisation
\i init_db.sql

# Quitter psql
\q
```

### Étape 3 — Configurer les variables d'environnement

```bash
# Éditer le fichier .env
cp .env .env.local
nano .env
```

Contenu du `.env` :
```
SECRET_KEY=votre-cle-secrete-ici
DEBUG=True
DB_NAME=uadb_db
DB_USER=uadb_user
DB_PASSWORD=uadb_pass
DB_HOST=localhost
DB_PORT=5432

SERVICE_AUTH=http://localhost:8001
SERVICE_DOSSIER=http://localhost:8003
SERVICE_IA=http://localhost:8007
SERVICE_NOTIFICATION=http://localhost:8006

SERVICE_INTERNAL_USER=service_inscription
SERVICE_INTERNAL_PASSWORD=service_inscription_secret_2025
```

### Étape 4 — Appliquer les migrations

```bash
# Initialiser le schéma PostgreSQL
python manage.py init_schema

# Appliquer les migrations Django
python manage.py migrate

# Vérifier les migrations
python manage.py showmigrations
```

### Étape 5 — Lancer le serveur

```bash
# Développement
python manage.py runserver 8002

# Le service est accessible sur : http://localhost:8002
```

---

## Endpoints disponibles

| Méthode | URL | Rôle requis | Description |
|---------|-----|-------------|-------------|
| POST | `/api/inscriptions/` | etudiant | Soumettre une préinscription |
| POST | `/api/inscriptions/auto-create/` | interne (service dossier) | Créer automatiquement une inscription depuis un dossier validé |
| GET | `/api/inscriptions/mon-inscription/` | etudiant | Consulter son inscription |
| GET | `/api/inscriptions/mes-inscriptions/` | etudiant | Historique des inscriptions |
| GET | `/api/inscriptions/liste/` | agent_scolarite, admin | Lister toutes les inscriptions |
| GET | `/api/inscriptions/statistiques/` | admin | Tableau de bord statistiques |
| GET | `/api/inscriptions/{id}/` | agents, admin | Détail d'une inscription |
| PATCH | `/api/inscriptions/{id}/valider-etape/` | agents | Valider/rejeter une étape |
| GET | `/api/inscriptions/{id}/workflow/` | tous | État du circuit de validation |
| GET | `/api/inscriptions/{id}/paiement/` | tous | Consulter le paiement |
| POST | `/api/inscriptions/{id}/paiement/` | etudiant | Soumettre la preuve/transaction de paiement |
| PATCH | `/api/inscriptions/{id}/paiement/` | agent_comptable | Confirmer et enregistrer le paiement |
| GET | `/api/workflows/etapes-bloquees/` | interne (service IA) | Étapes en retard |

---

## Exemples d'appels API

### 1. Préinscription (étudiant)

```bash
curl -X POST http://localhost:8002/api/inscriptions/ \
  -H "Authorization: Bearer <token_etudiant>" \
  -H "Content-Type: application/json" \
  -d '{
    "formation_id": 1,
    "annee_universitaire": "2024-2025",
    "type_inscription": "premiere"
  }'
```

**Réponse :**
```json
{
  "id": 1,
  "etudiant_id": 42,
  "formation_id": 1,
  "annee_universitaire": "2024-2025",
  "statut_inscription": "en_cours",
  "numero_provisoire": "PROV-2025-000001",
  "numero_matricule": null,
  "workflow": {
    "statut": "en_cours",
    "etape_courante": 1,
    "progression": 0,
    "etapes": [
      {"ordre": 1, "nom": "Vérification scolarité",    "statut": "en_cours"},
      {"ordre": 2, "nom": "Vérification paiement",     "statut": "en_attente"},
      {"ordre": 3, "nom": "Visite médicale",           "statut": "en_attente"},
      {"ordre": 4, "nom": "Vérification bibliothèque", "statut": "en_attente"}
    ]
  }
}
```

### 2. Valider l'étape scolarité (agent scolarité)

```bash
curl -X PATCH http://localhost:8002/api/inscriptions/1/valider-etape/ \
  -H "Authorization: Bearer <token_agent_scolarite>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "valider",
    "observation": "Dossier complet et conforme."
  }'
```

### 3. Soumettre un paiement (étudiant)

Le montant dû est calculé automatiquement selon le niveau de la formation.

```bash
curl -X POST http://localhost:8002/api/inscriptions/1/paiement/ \
  -H "Authorization: Bearer <token_etudiant>" \
  -H "Content-Type: application/json" \
  -d '{
    "montant_paye": 50000,
    "mode_paiement": "orange_money",
    "reference_paiement": "OM-2025-789456"
  }'
```

### 4. Confirmer le paiement (agent comptable)

Le champ `montant` n'est plus piloté par le body : il est fixé automatiquement
par le service selon le niveau de la formation.

```bash
curl -X PATCH http://localhost:8002/api/inscriptions/1/paiement/ \
  -H "Authorization: Bearer <token_agent_comptable>" \
  -H "Content-Type: application/json" \
  -d '{
    "montant_paye": 50000,
    "mode_paiement": "orange_money",
    "reference_paiement": "OM-2025-789456"
  }'
```

### 5. Consulter l'état du workflow (étudiant)

```bash
curl -X GET "http://localhost:8002/api/inscriptions/mon-inscription/?annee=2024-2025" \
  -H "Authorization: Bearer <token_etudiant>"
```

---

## Tarification des frais d'inscription

Le montant est déterminé automatiquement à partir du `niveau` de la formation
(référentiel du `dossier_service`) :

| Niveau | Frais |
|--------|-------|
| `L1`, `L2`, `L3` | `25000 FCFA` |
| `M1`, `M2` | `50000 FCFA` |

Si la formation est indisponible ou son niveau non reconnu, le service renvoie
une erreur (`503`) au moment du paiement.

---

## Rôles JWT requis

Le token JWT doit contenir le champ `roles` avec les valeurs suivantes :

| Rôle | Accès |
|------|-------|
| `etudiant` | Préinscription, consultation de sa propre inscription |
| `agent_scolarite` | Liste toutes les inscriptions, valide étape scolarité |
| `agent_comptable` | Enregistre paiement, valide étape comptabilité |
| `service_medical` | Valide étape médicale |
| `bibliotheque` | Valide étape bibliothèque |
| `admin` | Accès total + statistiques |

**Exemple de payload JWT :**
```json
{
  "user_id": 5,
  "login": "agent_scolarite_01",
  "email": "scolarite@uadb.edu.sn",
  "roles": ["agent_scolarite"],
  "etat": "actif",
  "etudiant_id": null
}
```

---

## Fonctionnement du workflow automatique

Le circuit de validation fonctionne entièrement via les **signaux Django**.
Aucune intervention manuelle n'est nécessaire pour faire avancer le circuit.

### Création d'inscription depuis dossier validé

Quand un dossier passe à l'état `valide` dans `dossier_service`,
`inscription_service` crée automatiquement l'inscription (même étudiant,
même formation, même année universitaire). L'opération est idempotente :
si une inscription existe déjà pour l'année, elle est réutilisée.

```
Étudiant soumet préinscription
        ↓
Signal post_save (Inscription)
        ↓
Création automatique :
  → numéro provisoire (PROV-2025-000001)
  → 4 ValidationService (en_attente)
  → 1 Workflow (en_cours)
  → 4 EtapeWorkflow (étape 1 active)
  → Notification scolarité
        ↓
Agent scolarité valide
        ↓
Signal post_save (ValidationService)
        ↓
Étape 1 → validée
Étape 2 → activée
Notification comptabilité
        ↓
Agent comptable valide
        ↓
... (même logique pour médical et bibliothèque)
        ↓
Toutes les étapes validées
        ↓
finaliser_inscription()
  → Workflow terminé
  → Matricule généré (UADB-2025-000001)
  → Inscription validée
  → Notification étudiant
```

---

## Tests rapides

```bash
# Vérifier que le serveur répond
curl http://localhost:8002/api/inscriptions/liste/ \
  -H "Authorization: Bearer <token>"

# Vérifier les migrations
python manage.py showmigrations

# Accéder à l'interface admin Django
# http://localhost:8002/admin/
python manage.py createsuperuser
```
