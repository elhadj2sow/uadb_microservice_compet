# Microservice IA & Moteur de Règles — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
ia_service/
├── .env
├── requirements.txt
├── manage.py
├── init_db.sql
├── ia_service/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── moteur/
    ├── __init__.py
    ├── models.py          ← RegleMetier, MoteurDecision,
    │                        DecisionAutomatique, AlerteAnomalie
    ├── engine.py          ← Cœur du moteur de règles
    ├── services.py        ← Services métier + dispatcher
    ├── serializers.py     ← Sérialisation DRF complète
    ├── views.py           ← Tous les endpoints REST
    ├── urls.py            ← Routage complet
    ├── permissions.py     ← Contrôle d'accès par rôle JWT
    ├── authentication.py  ← JWT inter-services
    ├── apps.py
    ├── admin.py
    ├── migrations/
    │   └── 0001_initial.py  ← Tables + 12 règles + moteur
    └── management/commands/
        └── init_schema.py
```

---

## Installation et démarrage

### Étape 1 — Installer les dépendances

```bash
cd ia_service
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
DEBUG=True
DB_NAME=uadb6_db
DB_USER=uadb6_user
DB_PASSWORD=uadb6_pass
DB_HOST=localhost
DB_PORT=5432

SERVICE_AUTH=http://localhost:8001
SERVICE_NOTIFICATION=http://localhost:8006

SERVICE_INTERNAL_USER=service_ia
SERVICE_INTERNAL_PASSWORD=service_ia_secret_2025
```

### Étape 4 — Appliquer les migrations

```bash
python manage.py init_schema
python manage.py migrate
# Insère automatiquement 12 règles métier + 1 instance moteur
```

### Étape 5 — Lancer le serveur

```bash
python manage.py runserver 8007
```

---

## Endpoints disponibles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| POST | `/api/evaluer/` | Tous (inter-services) | **Point d'entrée principal** |
| GET | `/api/regles/` | Tous | Lister les règles actives |
| POST | `/api/regles/` | Admin | Créer une règle |
| GET | `/api/regles/{id}/` | Admin | Détail d'une règle |
| PATCH | `/api/regles/{id}/` | Admin | Modifier une règle |
| DELETE | `/api/regles/{id}/` | Admin | Supprimer une règle |
| POST | `/api/regles/{id}/tester/` | Admin | Tester une règle |
| GET | `/api/decisions/` | Agents, Admin | Historique décisions |
| GET | `/api/decisions/{id}/` | Agents, Admin | Détail décision |
| GET | `/api/alertes/` | Agents, Admin | Alertes ouvertes |
| GET | `/api/alertes/{id}/` | Agents, Admin | Détail alerte |
| PATCH | `/api/alertes/{id}/resoudre/` | Agents, Admin | Résoudre alerte |
| GET | `/api/moteur/statut/` | Tous | Statut du moteur |
| GET | `/api/statistiques/` | Admin | Tableau de bord IA |

---

## Exemples d'appels API

### 1. Évaluer la complétude d'un dossier

```bash
curl -X POST http://localhost:8007/api/evaluer/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type"       : "completude_dossier",
    "etudiant"   : 42,
    "dossier_id" : 15,
    "score"      : 100
  }'
```

**Réponse :**
```json
{
  "eligible"   : true,
  "resultat"   : "complet",
  "motif"      : "Dossier complet à 100%",
  "confiance"  : 1.0,
  "decision_id": 23
}
```

### 2. Valider une délibération

```bash
curl -X POST http://localhost:8007/api/evaluer/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type"           : "validation_deliberation",
    "etudiant"       : 42,
    "deliberation_id": 5,
    "moyenne"        : 13.5,
    "credits"        : 60
  }'
```

**Réponse :**
```json
{
  "decision"   : "admis",
  "mention"    : "assez_bien",
  "motif"      : "Admission définitive",
  "confiance"  : 1.0,
  "decision_id": 24
}
```

### 3. Vérifier éligibilité attestation

```bash
curl -X POST http://localhost:8007/api/evaluer/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type"               : "eligibilite_attestation",
    "etudiant"           : 42,
    "type_att"           : "reussite",
    "inscription_validee": true,
    "decision"           : "admis"
  }'
```

**Réponse :**
```json
{
  "eligible"   : true,
  "resultat"   : "eligible",
  "motif"      : "Éligible — attestation de réussite",
  "confiance"  : 1.0,
  "decision_id": 25
}
```

### 4. Tester une règle (admin)

```bash
curl -X POST http://localhost:8007/api/regles/1/tester/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "contexte": {
      "score_completude": 85
    }
  }'
```

**Réponse :**
```json
{
  "regle_code": "DOSSIER_EN_COURS",
  "condition" : "contexte['score_completude'] >= 50 and contexte['score_completude'] < 100",
  "contexte"  : {"score_completude": 85},
  "resultat"  : true,
  "action"    : "en_cours",
  "message"   : "La règle se déclenche → action : en_cours"
}
```

### 5. Résoudre une alerte

```bash
curl -X PATCH http://localhost:8007/api/alertes/3/resoudre/ \
  -H "Authorization: Bearer <token_agent>" \
  -H "Content-Type: application/json" \
  -d '{
    "statut_traitement": "resolue",
    "note_resolution"  : "Dossier complété par l étudiant."
  }'
```

---

## Règles métier insérées automatiquement (12 règles)

### Domaine : dossier

| Code | Condition | Action |
|------|-----------|--------|
| `DOSSIER_COMPLET` | `score == 100` | `complet` |
| `DOSSIER_EN_COURS` | `50 ≤ score < 100` | `en_cours` |
| `DOSSIER_INCOMPLET` | `score < 50` | `incomplet` |

### Domaine : délibération

| Code | Condition | Action |
|------|-----------|--------|
| `DELIB_ADMIS` | `moyenne ≥ 10 ET crédits ≥ 60` | `admis` |
| `DELIB_RATTRAPAGE` | `8 ≤ moyenne < 10` | `rattrapage` |
| `DELIB_AJOURNE` | `moyenne < 8` | `ajourné` |

### Domaine : attestation

| Code | Condition | Action |
|------|-----------|--------|
| `ATT_INSCRIPTION_OK` | `inscription_validee == True` | `eligible` |
| `ATT_REUSSITE_OK` | `type in (reussite,passage) ET decision==admis` | `eligible` |
| `ATT_NON_ELIGIBLE` | `inscription_validee == False` | `non_eligible` |

### Domaine : inscription

| Code | Condition | Action |
|------|-----------|--------|
| `INSC_ELIGIBLE` | `score_dossier==100 ET paiement_confirme==True` | `eligible` |
| `INSC_DOSSIER_INCOMPLET` | `score_dossier < 100` | `dossier_incomplet` |
| `INSC_PAIEMENT_MANQUANT` | `paiement_confirme == False` | `paiement_manquant` |

---

## Ajouter une nouvelle règle

Via l'API (admin) ou l'interface Django Admin :

```bash
curl -X POST http://localhost:8007/api/regles/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "code_regle" : "DELIB_MENTION_TB",
    "libelle"    : "Mention Très Bien",
    "domaine"    : "deliberation",
    "condition"  : "contexte['"'"'moyenne'"'"'] >= 16",
    "action"     : "tres_bien",
    "priorite"   : 1,
    "active"     : true
  }'
```

**Important** : La condition doit utiliser `contexte['cle']`.
Les fonctions Python disponibles sont : `len`, `sum`, `min`, `max`,
`abs`, `round`, `all`, `any`, `int`, `float`, `str`, `bool`.

---

## Tables PostgreSQL créées

| Table | Description |
|-------|-------------|
| `ia.regle_metier` | Règles métier modifiables depuis l'admin |
| `ia.moteur_decision` | Instance singleton du moteur |
| `ia.decision_automatique` | Historique de toutes les décisions |
| `ia.alerte_anomalie` | Anomalies détectées par le moteur |

---

## Architecture du moteur

```
Appel POST /api/evaluer/
        ↓
EvaluerView → dispatcher(type, data)
        ↓
ServiceDossier | ServiceDeliberation
ServiceAttestation | ServiceInscription
        ↓
MoteurRegles(domaine)
  → charge les règles actives par priorité
  → évalue chaque condition : eval(condition, {contexte: data})
  → retourne la 1ère règle dont la condition est True
        ↓
tracer_decision() → DecisionAutomatique en base
        ↓
Retour JSON : {resultat, motif, confiance, decision_id}
```
