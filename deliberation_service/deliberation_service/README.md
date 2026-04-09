# Microservice Délibération — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
deliberation_service/
├── .env
├── requirements.txt
├── manage.py
├── init_db.sql
├── deliberation_service/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── deliberation/
    ├── __init__.py
    ├── models.py          ← Deliberation, Resultat, Note
    ├── serializers.py     ← sérialisation DRF complète
    ├── views.py           ← tous les endpoints REST
    ├── urls.py            ← routage complet
    ├── signals.py         ← calcul automatique des moyennes
    ├── pv_generator.py    ← génération PDF du PV (ReportLab)
    ├── utils.py           ← appel service IA + notifications
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
cd deliberation_service
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
DB_NAME=uadb_db
DB_USER=uadb_user
DB_PASSWORD=uadb_pass
DB_HOST=localhost
DB_PORT=5432

SERVICE_AUTH=http://localhost:8001
SERVICE_DOSSIER=http://localhost:8003
SERVICE_IA=http://localhost:8007
SERVICE_NOTIFICATION=http://localhost:8006

SERVICE_INTERNAL_USER=service_deliberation
SERVICE_INTERNAL_PASSWORD=service_deliberation_secret_2025
```

### Étape 4 — Appliquer les migrations

```bash
python manage.py init_schema
python manage.py migrate
```

### Étape 5 — Lancer le serveur

```bash
python manage.py runserver 8004
```

---

## Endpoints disponibles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| GET | `/api/deliberations/` | Jury, Admin | Lister les délibérations |
| POST | `/api/deliberations/` | Resp. pédago | Créer une délibération |
| GET | `/api/deliberations/statistiques/` | Admin | Tableau de bord |
| GET | `/api/deliberations/{id}/` | Jury | Détail délibération |
| PATCH | `/api/deliberations/{id}/` | Resp. pédago | Modifier |
| POST | `/api/deliberations/{id}/cloturer/` | Resp. pédago | Clôturer + rangs + notifs |
| GET | `/api/deliberations/{id}/pv/` | Jury | Télécharger PV PDF |
| GET | `/api/deliberations/{id}/resultats/` | Jury | Lister les résultats |
| POST | `/api/deliberations/{id}/resultats/` | Jury | Ajouter un étudiant |
| POST | `/api/deliberations/{id}/notes/bulk/` | Enseignant | Saisie en masse |
| GET | `/api/resultats/mes-resultats/` | Étudiant | Mes résultats |
| GET | `/api/resultats/{id}/` | Tous | Détail résultat |
| PATCH | `/api/resultats/{id}/` | Jury | Modifier décision |
| GET | `/api/resultats/{id}/notes/` | Tous | Notes d'un résultat |
| POST | `/api/resultats/{id}/notes/saisir/` | Enseignant | Saisir une note |

---

## Exemples d'appels API

### 1. Créer une délibération

```bash
curl -X POST http://localhost:8004/api/deliberations/ \
  -H "Authorization: Bearer <token_responsable>" \
  -H "Content-Type: application/json" \
  -d '{
    "session"            : "normale",
    "annee_universitaire": "2024-2025",
    "semestre"           : 1,
    "niveau"             : "M1",
    "formation_id"       : 2,
    "date_deliberation"  : "2025-01-20"
  }'
```

### 2. Ajouter un étudiant à la délibération

```bash
curl -X POST http://localhost:8004/api/deliberations/1/resultats/ \
  -H "Authorization: Bearer <token_responsable>" \
  -H "Content-Type: application/json" \
  -d '{
    "etudiant_id"   : 42,
    "inscription_id": 15,
    "credits_total" : 60
  }'
```

### 3. Saisir les notes d'un étudiant (enseignant)

```bash
curl -X POST http://localhost:8004/api/resultats/1/notes/saisir/ \
  -H "Authorization: Bearer <token_enseignant>" \
  -H "Content-Type: application/json" \
  -d '{
    "ue_id"         : 5,
    "code_ue"       : "INF401",
    "libelle_ue"    : "Bases de données avancées",
    "credit_ue"     : 4,
    "coefficient_ue": 2.0,
    "semestre"      : 1,
    "note_cc"       : 14.5,
    "note_tp"       : 16.0,
    "note_examen"   : 13.0
  }'
```

**Réponse — la moyenne est calculée automatiquement :**
```json
{
  "message": "Note créée avec succès.",
  "note": {
    "id"            : 1,
    "code_ue"       : "INF401",
    "note_cc"       : "14.50",
    "note_tp"       : "16.00",
    "note_examen"   : "13.00",
    "valeur"        : "13.75",
    "est_validee"   : true
  }
}
```

### 4. Saisie en masse (import notes)

```bash
curl -X POST http://localhost:8004/api/deliberations/1/notes/bulk/ \
  -H "Authorization: Bearer <token_enseignant>" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "etudiant_id": 42,
      "notes": [
        {"ue_id": 5, "code_ue": "INF401", "note_examen": 13.0},
        {"ue_id": 6, "code_ue": "INF402", "note_examen": 15.5}
      ]
    },
    {
      "etudiant_id": 43,
      "notes": [
        {"ue_id": 5, "code_ue": "INF401", "note_examen": 9.0},
        {"ue_id": 6, "code_ue": "INF402", "note_examen": 11.0}
      ]
    }
  ]'
```

### 5. Clôturer la délibération

```bash
curl -X POST http://localhost:8004/api/deliberations/1/cloturer/ \
  -H "Authorization: Bearer <token_responsable>" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_finale": "Session normale 2024-2025 clôturée.",
    "observation"    : "Taux de réussite : 78%"
  }'
```

### 6. Télécharger le PV PDF

```bash
curl -X GET http://localhost:8004/api/deliberations/1/pv/ \
  -H "Authorization: Bearer <token_jury>" \
  --output PV_deliberation.pdf
```

### 7. Étudiant consulte ses résultats

```bash
curl http://localhost:8004/api/resultats/mes-resultats/ \
  -H "Authorization: Bearer <token_etudiant>"
```

---

## Fonctionnement automatique

### Calcul des moyennes (signal Django)

```
Enseignant saisit une note (POST /resultats/{id}/notes/saisir/)
        ↓
Sauvegarde Note en base
        ↓
Signal post_save (Note)
        ↓
recalculer_moyenne() :
  → calcule valeur UE : CC×30% + TP×20% + Examen×50%
  → recalcule moyenne pondérée du Resultat
  → appelle service IA pour décision + mention
  → met à jour Resultat.moyenne_annuelle, decision, mention
```

### Clôture de la délibération

```
POST /deliberations/{id}/cloturer/
        ↓
Verrouillage de toutes les notes (verrouille=True)
        ↓
Calcul des rangs (ordre décroissant par moyenne)
        ↓
Mise à jour statut délibération → "cloturee"
        ↓
Notification de chaque étudiant (email)
  → "Votre décision : Admis. Moyenne : 14.50/20"
```

---

## Tables PostgreSQL créées

| Table | Description |
|-------|-------------|
| `deliberation.deliberation` | Sessions de jury |
| `deliberation.resultat` | Résultats par étudiant par session |
| `deliberation.note` | Notes par UE par étudiant |

---

## Règles de calcul des notes

| Type | Poids |
|------|-------|
| Contrôle continu (CC) | 30% |
| Travaux pratiques (TP) | 20% |
| Examen final | 50% |

**Règles de décision (service IA ou secours local) :**

| Condition | Décision |
|-----------|----------|
| Moyenne ≥ 10 ET crédits ≥ 60 | Admis |
| 8 ≤ Moyenne < 10 | Rattrapage |
| Moyenne < 8 | Ajourné |

**Mentions :**

| Moyenne | Mention |
|---------|---------|
| ≥ 16 | Très Bien |
| ≥ 14 | Bien |
| ≥ 12 | Assez Bien |
| ≥ 10 | Passable |
