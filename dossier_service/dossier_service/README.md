# Microservice Dossier — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
dossier_service/
├── .env                               ← variables d'environnement
├── requirements.txt                   ← dépendances Python
├── manage.py
├── init_db.sql                        ← script SQL d'initialisation PostgreSQL
├── dossier_service/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── dossier/
    ├── __init__.py
    ├── models.py         ← Formation, UniteEnseignement,
    │                        DossierEtudiant, PieceJustificative
    ├── serializers.py    ← sérialisation DRF complète
    ├── views.py          ← tous les endpoints REST
    ├── urls.py           ← routage complet
    ├── signals.py        ← calcul automatique score complétude
    ├── storage.py        ← gestion MinIO (upload/download/delete)
    ├── permissions.py    ← contrôle d'accès par rôle JWT
    ├── authentication.py ← JWT inter-services
    ├── apps.py           ← connexion des signaux
    ├── admin.py          ← interface d'administration
    ├── migrations/
    │   └── 0001_initial.py  ← migration + formations UADB initiales
    └── management/commands/
        └── init_schema.py   ← commande d'initialisation du schéma
```

---

## Installation et démarrage

### Étape 1 — Installer les dépendances

```bash
cd dossier_service
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Étape 2 — Initialiser PostgreSQL

```bash
# Si la base n'existe pas encore (premier microservice)
psql -U postgres -f init_db.sql

# Si auth_service a déjà créé la base, juste créer le schéma :
psql -U postgres -d uadb_db -c "CREATE SCHEMA IF NOT EXISTS dossier AUTHORIZATION uadb_user;"
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

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uadb-dossiers
MINIO_USE_SSL=False

SERVICE_AUTH=http://localhost:8001
SERVICE_INSCRIPTION=http://localhost:8002
SERVICE_IA=http://localhost:8007
SERVICE_NOTIFICATION=http://localhost:8006

SERVICE_INTERNAL_USER=service_dossier
SERVICE_INTERNAL_PASSWORD=service_dossier_secret_2025
```

### Étape 4 — Démarrer MinIO (stockage fichiers)

```bash
# Avec Docker
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# Interface MinIO disponible sur : http://localhost:9001
```

### Étape 5 — Appliquer les migrations

```bash
# Créer le schéma PostgreSQL
python manage.py init_schema

# Appliquer les migrations Django
# (crée les 4 tables + insère les 5 formations UADB)
python manage.py migrate
```

### Étape 6 — Lancer le serveur

```bash
python manage.py runserver 8003
# Service accessible sur : http://localhost:8003
```

---

## Endpoints disponibles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| GET | `/api/formations/` | Tous | Lister les formations actives |
| GET | `/api/formations/{id}/` | Tous | Détail formation + UEs |
| POST | `/api/formations/creer/` | Admin | Créer une formation |
| PATCH | `/api/formations/{id}/modifier/` | Admin | Modifier une formation |
| GET | `/api/formations/{id}/ues/` | Tous | UEs d'une formation |
| POST | `/api/dossiers/` | Étudiant | Créer son dossier |
| GET | `/api/dossiers/mon-dossier/` | Étudiant | Consulter son dossier |
| GET | `/api/dossiers/mes-dossiers/` | Étudiant | Historique dossiers |
| GET | `/api/dossiers/liste/` | Agents | Lister tous les dossiers |
| GET | `/api/dossiers/statistiques/` | Admin | Tableau de bord |
| GET | `/api/dossiers/incomplets/` | Interne (IA) | Dossiers incomplets |
| GET | `/api/dossiers/{id}/` | Tous | Détail dossier |
| PATCH | `/api/dossiers/{id}/` | Agent scolarité | Valider/rejeter dossier |
| POST | `/api/dossiers/{id}/pieces/` | Étudiant | Déposer une pièce |
| GET | `/api/dossiers/{id}/pieces/liste/` | Tous | Lister les pièces |
| PATCH | `/api/pieces/{id}/verifier/` | Agent scolarité | Valider/rejeter pièce |
| GET | `/api/pieces/{id}/telecharger/` | Tous | URL téléchargement |
| DELETE | `/api/pieces/{id}/` | Étudiant | Supprimer pièce rejetée |

---

## Exemples d'appels API

### 1. Créer un dossier (étudiant)

```bash
curl -X POST http://localhost:8003/api/dossiers/ \
  -H "Authorization: Bearer <token_etudiant>" \
  -H "Content-Type: application/json" \
  -d '{
    "formation": 2,
    "annee_universitaire": "2024-2025"
  }'
```

**Réponse :**
```json
{
  "id": 1,
  "etudiant_id": 15,
  "formation": 2,
  "formation_detail": {
    "code_formation": "M1-SI",
    "libelle": "Master 1 Systèmes d'Information",
    "niveau": "M1"
  },
  "annee_universitaire": "2024-2025",
  "etat_dossier": "en_cours",
  "score_completude": 0,
  "pieces": [],
  "pieces_manquantes": [
    "bac", "cni", "photo", "acte_naissance",
    "certificat_medical", "quitus_bibliotheque", "recu_paiement"
  ],
  "pieces_expirees": []
}
```

### 2. Déposer une pièce justificative (étudiant)

```bash
curl -X POST http://localhost:8003/api/dossiers/1/pieces/ \
  -H "Authorization: Bearer <token_etudiant>" \
  -F "type_piece=bac" \
  -F "fichier=@/chemin/vers/bac.pdf" \
  -F "est_obligatoire=true"
```

**Réponse :**
```json
{
  "id": 1,
  "type_piece": "bac",
  "nom_fichier": "bac.pdf",
  "taille_fichier": 245760,
  "type_mime": "application/pdf",
  "statut_verification": "en_attente",
  "est_obligatoire": true,
  "date_depot": "2025-01-15T10:30:00Z",
  "url_telechargement": "http://localhost:9000/uadb-dossiers/..."
}
```

### 3. Valider une pièce (agent scolarité)

```bash
curl -X PATCH http://localhost:8003/api/pieces/1/verifier/ \
  -H "Authorization: Bearer <token_agent_scolarite>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "valider"
  }'
```

### 4. Rejeter une pièce avec motif (agent scolarité)

```bash
curl -X PATCH http://localhost:8003/api/pieces/2/verifier/ \
  -H "Authorization: Bearer <token_agent_scolarite>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "rejeter",
    "motif_rejet": "Photo illisible, veuillez uploader une photo plus claire."
  }'
```

### 5. Consulter son dossier avec score (étudiant)

```bash
curl http://localhost:8003/api/dossiers/mon-dossier/?annee=2024-2025 \
  -H "Authorization: Bearer <token_etudiant>"
```

---

## Fonctionnement du calcul automatique

Le score de complétude se recalcule automatiquement
via un signal Django à chaque dépôt ou vérification de pièce.

```
Étudiant dépose une pièce (POST /dossiers/{id}/pieces/)
        ↓
Upload fichier sur MinIO
        ↓
Création PieceJustificative en base
        ↓
Signal post_save (PieceJustificative)
        ↓
recalculer_completude() :
  → compte les pièces obligatoires validées
  → calcule score = (validées / 7) × 100
  → met à jour etat_dossier
        ↓
Si score == 100% :
  → Notification étudiant (email)
  → Appel service IA pour traçabilité
```

**Pièces obligatoires (7) :**

| Type | Description |
|------|-------------|
| `bac` | Baccalauréat |
| `cni` | Carte Nationale d'Identité |
| `photo` | Photo d'identité |
| `acte_naissance` | Acte de naissance |
| `certificat_medical` | Certificat médical |
| `quitus_bibliotheque` | Quitus bibliothèque |
| `recu_paiement` | Reçu de paiement |

---

## Formations insérées automatiquement

| Code | Libellé | Niveau |
|------|---------|--------|
| `L3-INFO` | Licence 3 Informatique | L3 |
| `M1-SI` | Master 1 Systèmes d'Information | M1 |
| `M2-SI` | Master 2 Systèmes d'Information | M2 |
| `M1-SR` | Master 1 Systèmes et Réseaux | M1 |
| `M2-SR` | Master 2 Systèmes et Réseaux | M2 |

---

## Tables PostgreSQL créées

| Table | Description |
|-------|-------------|
| `dossier.formation` | Référentiel des formations UADB |
| `dossier.unite_enseignement` | UEs de chaque formation |
| `dossier.dossier_etudiant` | Dossiers administratifs étudiants |
| `dossier.piece_justificative` | Pièces justificatives (chemin MinIO) |
