# Microservice Attestation — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
attestation_service/
├── .env
├── requirements.txt
├── manage.py
├── init_db.sql
├── attestation_service/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── attestation/
    ├── __init__.py
    ├── models.py          ← DemandeAttestation, Attestation
    ├── serializers.py     ← sérialisation DRF complète
    ├── views.py           ← tous les endpoints REST
    ├── urls.py            ← routage complet
    ├── services.py        ← pipeline complet en 8 étapes
    ├── pdf_generator.py   ← génération PDF + QR code (ReportLab)
    ├── storage.py         ← gestion MinIO (PDF + images)
    ├── utils.py           ← appels inter-services + règles secours
    ├── permissions.py     ← contrôle d'accès par rôle JWT
    ├── authentication.py  ← JWT inter-services
    ├── apps.py
    ├── admin.py
    ├── migrations/
    │   └── 0001_initial.py
    └── management/commands/
        └── init_schema.py
```

---

## Installation et démarrage

### Étape 1 — Installer les dépendances

```bash
cd attestation_service
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
JWT_SIGNING_KEY=cle-jwt-partagee-entre-services
DEBUG=True
DB_NAME=uadb4_db
DB_USER=uadb4_user
DB_PASSWORD=uadb4_pass
DB_HOST=localhost
DB_PORT=5432

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uadb-attestations
MINIO_USE_SSL=False

SERVICE_AUTH=http://localhost:8001
SERVICE_INSCRIPTION=http://localhost:8002
SERVICE_DELIBERATION=http://localhost:8004
SERVICE_IA=http://localhost:8007
SERVICE_NOTIFICATION=http://localhost:8006

SERVICE_INTERNAL_USER=service_attestation
SERVICE_INTERNAL_PASSWORD=service_attestation_secret_2025

PORTAIL_URL=https://uadb.edu.sn
```

### Étape 4 — Démarrer MinIO

```bash
docker run -d \
  --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### Étape 5 — Appliquer les migrations

```bash
python manage.py init_schema
python manage.py migrate
```

### Étape 6 — Lancer le serveur

```bash
python manage.py runserver 8005
```

---

## Endpoints disponibles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| POST | `/api/attestations/demandes/` | Étudiant | Soumettre une demande |
| GET | `/api/attestations/mes-demandes/` | Étudiant | Mes demandes + attestations |
| GET | `/api/attestations/demandes/{id}/` | Étudiant | Détail d'une demande |
| GET | `/api/attestations/{id}/telecharger/` | Tous | URL téléchargement PDF |
| POST | `/api/attestations/demandes/{id}/regenerer/` | Agent scolarité | Regénérer le PDF |
| GET | `/api/attestations/verifier/{code}/` | **PUBLIC** | Vérifier authenticité |
| GET | `/api/attestations/admin/demandes/` | Agents, Admin | Lister toutes les demandes |
| GET | `/api/attestations/admin/demandes/{id}/` | Agents, Admin | Détail demande |
| PATCH | `/api/attestations/admin/demandes/{id}/` | Agents, Admin | Approuver / refuser |
| GET | `/api/attestations/statistiques/` | Admin | Tableau de bord |

---

## Exemples d'appels API

### 1. Soumettre une demande d'attestation d'inscription

```bash
curl -X POST http://localhost:8005/api/attestations/demandes/ \
  -H "Authorization: Bearer <token_etudiant>" \
  -H "Content-Type: application/json" \
  -d '{
    "type_attestation"    : "inscription",
    "annee_universitaire" : "2024-2025",
    "motif"               : "Demande de bourse CROUS"
  }'
```

**Réponse si éligible (traitement immédiat) :**
```json
{
  "message"    : "Attestation générée avec succès. Vous pouvez la télécharger maintenant.",
  "numero"     : "ATT-2025-000001",
  "code_verif" : "a1b2c3d4-e5f6-...",
  "demande": {
    "id"              : 1,
    "type_attestation": "inscription",
    "statut"          : "generee",
    "attestation": {
      "numero_ordre"      : "ATT-2025-000001",
      "statut_attestation": "generee",
      "date_generation"   : "2025-01-15T10:30:00Z",
      "url_telechargement": "http://localhost:9000/uadb-attestations/..."
    }
  }
}
```

**Réponse si non éligible :**
```json
{
  "message"    : "Demande traitée.",
  "statut"     : "refusee",
  "motif_refus": "Inscription non validée.",
  "demande"    : { "statut": "refusee", ... }
}
```

### 2. Télécharger l'attestation

```bash
curl http://localhost:8005/api/attestations/1/telecharger/ \
  -H "Authorization: Bearer <token_etudiant>"
```

**Réponse :**
```json
{
  "url"        : "http://localhost:9000/uadb-attestations/attestations/2025/ATT-2025-000001.pdf?...",
  "numero"     : "ATT-2025-000001",
  "type"       : "inscription",
  "expiration" : "5 minutes"
}
```

### 3. Vérifier l'authenticité (PUBLIC — sans token)

```bash
curl http://localhost:8005/api/attestations/verifier/a1b2c3d4e5f6.../
```

**Réponse si valide :**
```json
{
  "valide"             : true,
  "numero"             : "ATT-2025-000001",
  "type"               : "Attestation d'inscription",
  "annee_universitaire": "2024-2025",
  "date_generation"    : "2025-01-15T10:30:00Z",
  "statut"             : "delivree",
  "message"            : "Ce document est authentique et a été émis par l'Université Alioune Diop de Bambey."
}
```

**Réponse si invalide :**
```json
{
  "valide" : false,
  "message": "Ce document est introuvable ou invalide..."
}
```

### 4. Agent approuve manuellement une demande

```bash
curl -X PATCH http://localhost:8005/api/attestations/admin/demandes/1/ \
  -H "Authorization: Bearer <token_agent_scolarite>" \
  -H "Content-Type: application/json" \
  -d '{"action": "approuver"}'
```

### 5. Agent refuse une demande

```bash
curl -X PATCH http://localhost:8005/api/attestations/admin/demandes/1/ \
  -H "Authorization: Bearer <token_agent_scolarite>" \
  -H "Content-Type: application/json" \
  -d '{
    "action"     : "refuser",
    "motif_refus": "Inscription non finalisée pour cette année."
  }'
```

---

## Pipeline automatique de traitement

```
Étudiant POST /api/attestations/demandes/
        ↓
Création DemandeAttestation (statut=en_attente)
        ↓
AttestationService.traiter_demande()
        ↓
1. Récupérer inscription (service inscription :8002)
2. Récupérer résultat délibération (service délibération :8004)
3. Récupérer profil étudiant (service auth :8001)
        ↓
4. Vérifier éligibilité (service IA :8007)
   → eligible=False : demande refusée + notification
   → eligible=True  : continuer
        ↓
5. Créer Attestation en base + générer numéro ATT-2025-000001
        ↓
6. Générer QR code → stocker sur MinIO (qrcodes/...)
        ↓
7. Générer PDF avec ReportLab :
   - En-tête institutionnel UADB
   - Corps selon type (inscription / réussite / passage...)
   - Informations étudiant (nom, matricule)
   - Signature + QR code côte à côte
   - Pied de page avec code de vérification
        ↓
8. Stocker PDF sur MinIO (attestations/2025/ATT-2025-000001.pdf)
        ↓
9. Finaliser : statut=generee, date_traitement=now()
        ↓
10. Notifier étudiant (email) : "Votre attestation est disponible"
        ↓
Retourner l'attestation à React
```

---

## Types d'attestations supportés

| Type | Description | Condition |
|------|-------------|-----------|
| `inscription` | Attestation d'inscription | Inscription validée |
| `scolarite` | Certificat de scolarité | Inscription validée |
| `passage` | Attestation de passage | Délibération : admis |
| `reussite` | Attestation de réussite | Délibération : admis |
| `releve_notes` | Relevé de notes | Inscription validée |

---

## Tables PostgreSQL créées

| Table | Description |
|-------|-------------|
| `attestation.demande_attestation` | Demandes soumises par les étudiants |
| `attestation.attestation` | Documents générés avec code QR et PDF |

---

## Vérification QR Code

Chaque attestation contient un QR code qui pointe vers :
```
https://uadb.edu.sn/verifier/{code_verification}
```

Ce lien renvoie vers l'endpoint public `/api/attestations/verifier/{code}/`
qui ne nécessite **aucune authentification** et confirme l'authenticité
du document en moins d'une seconde.
