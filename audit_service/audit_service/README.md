# Microservice Audit — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
audit_service/
├── .env
├── requirements.txt
├── manage.py
├── init_db.sql
├── audit_service/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── audit/
    ├── __init__.py
    ├── models.py          ← JournalAudit, StatistiqueAudit
    ├── serializers.py     ← Sérialisation DRF complète
    ├── views.py           ← Tous les endpoints REST
    ├── urls.py            ← Routage complet
    ├── utils.py           ← Fonctions tracer() + calculer_statistiques()
    ├── permissions.py     ← Contrôle d'accès par rôle JWT
    ├── authentication.py  ← JWT inter-services
    ├── apps.py
    ├── admin.py
    ├── migrations/
    │   └── 0001_initial.py  ← Tables + 5 index de performance
    └── management/commands/
        └── init_schema.py
```

---

## Installation et démarrage

### Étape 1 — Installer les dépendances

```bash
cd audit_service
python -m venv venv
source venv/bin/activate    # Linux / Mac
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Étape 2 — Initialiser PostgreSQL

```bash
psql -U postgres -f init_db.sql
```

### Étape 3 — Configurer le fichier .env

```
SECRET_KEY=changez-cette-cle
JWT_SIGNING_KEY=changez-cette-cle-du-auth-service
DEBUG=True
DB_NAME=uadb7_db
DB_USER=uadb7_user
DB_PASSWORD=uadb7_pass
DB_HOST=localhost
DB_PORT=5432
SERVICE_AUTH=http://localhost:8001
SERVICE_INTERNAL_USER=service_audit
SERVICE_INTERNAL_PASSWORD=service_audit_secret_2025
RETENTION_JOURS=365
```

### Étape 4 — Appliquer les migrations

```bash
python manage.py init_schema
python manage.py migrate
```

### Étape 5 — Lancer le serveur

```bash
python manage.py runserver 8008
```

---

## Endpoints disponibles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| POST | `/api/audit/tracer/` | Tous (inter-services) | **Tracer une action** |
| GET | `/api/audit/journal/` | Agents, Admin | Journal avec filtres |
| GET | `/api/audit/journal/{id}/` | Agents, Admin | Détail d'une entrée |
| GET | `/api/audit/etudiants/{id}/journal/` | Agents, Admin | Journal d'un étudiant |
| GET | `/api/audit/utilisateurs/{id}/journal/` | Admin | Journal d'un utilisateur |
| GET | `/api/audit/statistiques/` | Admin | Tableau de bord |
| GET | `/api/audit/statistiques/daily/` | Admin | Stats par jour (7j) |
| POST | `/api/audit/statistiques/calculer/` | Admin | Recalculer les stats |
| DELETE | `/api/audit/purger/` | Admin | Purger les vieux logs |
| GET | `/api/audit/meta/` | Tous | Choix disponibles |

---

## Exemples d'appels API

### 1. Tracer une action depuis un microservice

```bash
curl -X POST http://localhost:8008/api/audit/tracer/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action"         : "VALIDATE",
    "service"        : "inscription",
    "utilisateur_id" : 5,
    "acteur"         : "agent_scolarite_01",
    "role_acteur"    : "agent_scolarite",
    "description"    : "Validation étape scolarité — inscription ID:15",
    "ressource"      : "inscription/15",
    "ressource_id"   : 15,
    "ressource_type" : "Inscription",
    "etudiant_id"    : 42,
    "inscription_id" : 15,
    "niveau"         : "INFO",
    "statut"         : "succes"
  }'
```

### 2. Tracer une connexion échouée

```bash
curl -X POST http://localhost:8008/api/audit/tracer/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "action"     : "LOGIN_ECHEC",
    "service"    : "auth",
    "acteur"     : "amadou.diallo",
    "description": "Tentative de connexion échouée — mot de passe incorrect",
    "niveau"     : "WARNING",
    "statut"     : "echec",
    "adresse_ip" : "196.14.22.5"
  }'
```

### 3. Consulter le journal avec filtres

```bash
# Toutes les actions d'un étudiant
curl "http://localhost:8008/api/audit/etudiants/42/journal/" \
  -H "Authorization: Bearer <token_agent>"

# Actions en échec du service inscription
curl "http://localhost:8008/api/audit/journal/?service=inscription&statut=echec" \
  -H "Authorization: Bearer <token_admin>"

# Actions WARNING et CRITICAL
curl "http://localhost:8008/api/audit/journal/?niveau=WARNING&date_debut=2025-01-01" \
  -H "Authorization: Bearer <token_admin>"
```

### 4. Tableau de bord statistiques

```bash
curl "http://localhost:8008/api/audit/statistiques/?date_debut=2025-01-01&date_fin=2025-01-31" \
  -H "Authorization: Bearer <token_admin>"
```

### 5. Purger les anciens logs (admin)

```bash
curl -X DELETE http://localhost:8008/api/audit/purger/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{"retention_jours": 365}'
```

---

## Comment intégrer l'audit dans les autres services

Ajoutez cet appel dans chaque vue sensible de vos microservices :

```python
# Dans n'importe quel service Django
import requests

def tracer_audit(action, service, **kwargs):
    try:
        requests.post(
            'http://localhost:8008/api/audit/tracer/',
            json={'action': action, 'service': service, **kwargs},
            headers={'Authorization': f'Bearer {get_internal_token()}'},
            timeout=3
        )
    except Exception:
        pass  # Ne jamais bloquer le service principal si l'audit échoue
```

---

## Actions disponibles

| Code | Description |
|------|-------------|
| `LOGIN` | Connexion réussie |
| `LOGOUT` | Déconnexion |
| `LOGIN_ECHEC` | Tentative échouée |
| `RESET_PWD` | Réinitialisation mot de passe |
| `CREATE` | Création d'une ressource |
| `UPDATE` | Modification |
| `DELETE` | Suppression |
| `READ` | Consultation |
| `VALIDATE` | Validation (étape workflow, dossier...) |
| `REJECT` | Rejet |
| `SUBMIT` | Soumission (inscription, demande...) |
| `UPLOAD` | Dépôt de fichier |
| `DOWNLOAD` | Téléchargement |
| `GENERATE` | Génération de document (attestation, PV...) |
| `VERIFY` | Vérification (pièce justificative...) |
| `DECISION_AUTO` | Décision automatique du moteur IA |
| `ALERTE` | Alerte anomalie détectée |
| `WORKFLOW_START` | Démarrage workflow inscription |
| `WORKFLOW_STEP` | Avancement d'une étape |
| `WORKFLOW_END` | Fin du workflow |
| `EXPORT` | Export de données |
| `CONFIG` | Modification de configuration |

---

## Tables PostgreSQL créées

| Table | Description |
|-------|-------------|
| `audit.journal_audit` | Journal de toutes les actions (avec 5 index) |
| `audit.statistique_audit` | Stats pré-calculées par jour |
