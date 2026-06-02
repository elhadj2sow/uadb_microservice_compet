# Architecture Générale du Système UADB — Microservices

## 1. Contexte et Objectif

Ce projet consiste en la conception et le développement d'un système d'information universitaire pour l'Université Alioune Diop de Bambey (UADB). Le système est structuré en **architecture microservices**, où chaque fonctionnalité métier est gérée par un service indépendant. L'ensemble est développé avec le framework **Django REST Framework (Python)** et une base de données **PostgreSQL**.

---

## 2. Liste des Microservices

| N° | Service | Port | Rôle principal |
|----|---------|------|----------------|
| 1 | **auth_service** | 8001 | Authentification, gestion des utilisateurs et rôles |
| 2 | **inscription_service** | 8002 | Préinscription, workflow d'inscription, paiement |
| 3 | **dossier_service** | 8003 | Dossier étudiant, pièces justificatives, formations |
| 4 | **deliberation_service** | 8004 | Délibérations, notes, résultats académiques |
| 5 | **notification_service** | 8006 | Envoi de notifications email/SMS, chatbot |
| 6 | **attestation_service** | 8007 | Demandes et génération d'attestations PDF |
| 7 | **ia_service** | 8008 | Moteur de règles métier et décisions automatiques |
| 8 | **audit_service** | 8009 | Journal centralisé de toutes les actions du système |

---

## 3. Principes d'Architecture

### 3.1 Isolation des Données
Chaque microservice possède sa **propre base de données PostgreSQL** (schéma séparé). Les microservices ne partagent jamais une table directement. Les références inter-services utilisent des **identifiants numériques (IDs)** sans clé étrangère réelle.

### 3.2 Communication Inter-Services
Les microservices communiquent via des **appels HTTP REST**. Pour les appels système (service à service), un token JWT interne est généré en se connectant avec un compte de service dédié.

```
Service A  ──→  POST /api/auth/login/ (compte interne)  ──→  auth_service
Service A  ──→  Bearer {token}  ──→  Service B
```

### 3.3 Authentification Centralisée (JWT)
- **Tous les services** valident les tokens JWT émis par `auth_service`.
- Le token contient : `user_id`, `username`, `roles`, `email`.
- La durée de vie du token est configurable (access token court, refresh token long).
- Le refresh token peut être **blacklisté** lors de la déconnexion.

### 3.4 Rôles et Permissions
Le système définit 8 rôles :

| Rôle | Description |
|------|-------------|
| `etudiant` | Accès à son dossier, ses inscriptions, ses résultats |
| `agent_scolarite` | Validation des dossiers et inscriptions |
| `agent_comptable` | Validation des paiements |
| `service_medical` | Validation de la visite médicale |
| `bibliotheque` | Gestion des emprunts et pénalités |
| `pedagogique` | Saisie des notes et gestion des délibérations |
| `admin` | Accès complet à tous les services |
| `super_admin` | Gestion système et configuration |

### 3.5 Stockage des Fichiers
Les fichiers (pièces justificatives, attestations PDF) sont stockés sur **MinIO** (système de stockage objet compatible S3). Seul le chemin du fichier est enregistré en base de données.

---

## 4. Flux Principal d'un Étudiant

```
1. Inscription          → L'étudiant crée son compte (auth_service)
2. Préinscription       → Il soumet sa demande d'inscription (inscription_service)
3. Constitution dossier → Il dépose ses pièces justificatives (dossier_service)
4. Validation workflow  → Scolarité, comptabilité, médical, bibliothèque valident (inscription_service)
5. Délibération         → Les notes sont saisies et le jury délibère (deliberation_service)
6. Attestation          → L'étudiant demande ses documents officiels (attestation_service)
7. Notifications        → À chaque étape, l'étudiant reçoit un email (notification_service)
8. Audit                → Chaque action est tracée dans le journal (audit_service)
```

---

## 5. Schéma de Communication

```
                    ┌─────────────────────────────────────────────┐
                    │              auth_service :8001              │
                    │     JWT · Utilisateurs · Rôles · Étudiants  │
                    └────────────────┬────────────────────────────┘
                                     │ JWT validation
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
  ┌───────▼──────┐          ┌────────▼──────┐         ┌────────▼──────┐
  │  inscription │          │    dossier    │         │ deliberation  │
  │   _service   │◄────────►│   _service   │◄────────►│   _service   │
  │    :8002     │          │    :8003     │         │    :8004     │
  └──────┬───────┘          └───────┬───────┘         └───────┬───────┘
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    │  notifications / audit
                    ┌───────────────▼──────────────────────┐
                    │    notification_service :8006         │
                    │    audit_service        :8009         │
                    │    attestation_service  :8007         │
                    │    ia_service           :8008         │
                    └──────────────────────────────────────┘
```

---

## 6. Technologies Utilisées

| Technologie | Usage |
|-------------|-------|
| Python 3.11 | Langage principal |
| Django 4.x | Framework web |
| Django REST Framework | API REST |
| SimpleJWT | Authentification JWT |
| PostgreSQL 15 | Base de données |
| MinIO | Stockage fichiers |
| ReportLab | Génération PDF |
| Requests | Communication HTTP inter-services |
| Django CORS Headers | Gestion CORS pour le frontend |

---

## 7. Structure Type d'un Service

Chaque microservice suit la même structure :

```
nom_service/
├── manage.py
├── requirements.txt
├── init_db.sql
├── .env
├── nom_service/          ← Configuration Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── app/                  ← Application Django
    ├── models.py         ← Modèles de données
    ├── serializers.py    ← Sérialisation REST
    ├── views.py          ← Logique métier
    ├── urls.py           ← Routes API
    ├── permissions.py    ← Contrôle d'accès
    ├── authentication.py ← Validation JWT
    └── migrations/       ← Migrations base de données
```
