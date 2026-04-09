# Microservice Notification & Chatbot — UADB
## Système d'Information Intelligent — Gestion Automatisée

---

## Structure du projet

```
notification_service/
├── .env
├── requirements.txt
├── manage.py
├── init_db.sql
├── notification_service/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── notification/
    ├── __init__.py
    ├── models.py          ← Notification, Conversation, Message, BaseConnaissance
    ├── serializers.py     ← sérialisation DRF complète
    ├── views.py           ← tous les endpoints REST
    ├── urls.py            ← routage complet
    ├── services.py        ← service d'envoi email/SMS
    ├── senders.py         ← envoi SMTP email + SMS Orange Sénégal
    ├── chatbot.py         ← moteur chatbot basé sur BaseConnaissance
    ├── permissions.py     ← contrôle d'accès par rôle JWT
    ├── authentication.py  ← JWT inter-services
    ├── apps.py
    ├── admin.py
    ├── migrations/
    │   └── 0001_initial.py  ← tables + 8 entrées base connaissance
    └── management/commands/
        └── init_schema.py
```

---

## Installation et démarrage

### Étape 1 — Installer les dépendances

```bash
cd notification_service
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
DB_NAME=uadb5_db
DB_USER=uadb5_user
DB_PASSWORD=uadb5_pass
DB_HOST=localhost
DB_PORT=5432

# Email SMTP Gmail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@uadb.edu.sn
EMAIL_HOST_PASSWORD=votre_mot_de_passe_app

# SMS Orange Sénégal (optionnel)
SMS_API_URL=https://api.orange.com/smsmessaging/v1/outbound
SMS_API_KEY=votre_cle_orange
SMS_SENDER=UADB

SERVICE_AUTH=http://localhost:8001
SERVICE_INTERNAL_USER=service_notification
SERVICE_INTERNAL_PASSWORD=service_notification_secret_2025
```

### Étape 4 — Appliquer les migrations

```bash
python manage.py init_schema
python manage.py migrate
# (insère automatiquement 8 entrées dans la base de connaissance)
```

### Étape 5 — Lancer le serveur

```bash
python manage.py runserver 8006
```

---

## Endpoints disponibles

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| POST | `/api/notifications/` | Tous (inter-services) | Envoyer une notification |
| GET | `/api/notifications/mes-notifications/` | Étudiant | Mes notifications |
| POST | `/api/notifications/tout-lire/` | Étudiant | Tout marquer comme lu |
| PATCH | `/api/notifications/{id}/lire/` | Étudiant | Marquer une notif comme lue |
| GET | `/api/notifications/admin/` | Agents, Admin | Toutes les notifications |
| POST | `/api/notifications/admin/relancer/` | Admin | Relancer les échecs |
| GET | `/api/notifications/statistiques/` | Admin | Tableau de bord |
| POST | `/api/chatbot/conversations/` | Étudiant | Démarrer une conversation |
| GET | `/api/chatbot/conversations/mes-conversations/` | Étudiant | Historique |
| GET | `/api/chatbot/conversations/{id}/` | Étudiant | Détail + messages |
| POST | `/api/chatbot/conversations/{id}/messages/` | Étudiant | Envoyer un message |
| DELETE | `/api/chatbot/conversations/{id}/` | Étudiant | Terminer la conversation |
| GET | `/api/chatbot/base-connaissance/` | Tous | Lister les entrées |
| POST | `/api/chatbot/base-connaissance/` | Admin | Ajouter une entrée |
| PATCH | `/api/chatbot/base-connaissance/{id}/` | Admin | Modifier une entrée |
| DELETE | `/api/chatbot/base-connaissance/{id}/` | Admin | Supprimer une entrée |
| POST | `/api/chatbot/tester/` | Admin | Tester le chatbot |

---

## Exemples d'appels API

### 1. Envoyer une notification (depuis un autre microservice)

```bash
curl -X POST http://localhost:8006/api/notifications/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "etudiant_id"      : 42,
    "canal"            : "email",
    "type_notification": "inscription",
    "message"          : "Votre inscription est validée. Matricule : UADB-2025-000042.",
    "emetteur_service" : "inscription_service",
    "inscription_id"   : 15
  }'
```

**Réponse :**
```json
{
  "message"     : "Notification traitée.",
  "id"          : 1,
  "statut_envoi": "envoye"
}
```

### 2. Notifier un service interne (workflow)

```bash
curl -X POST http://localhost:8006/api/notifications/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "service_destinataire": "scolarite",
    "canal"               : "interne",
    "type_notification"   : "workflow",
    "message"             : "Le dossier inscription ID:15 attend votre validation.",
    "emetteur_service"    : "inscription_service",
    "inscription_id"      : 15
  }'
```

### 3. Démarrer une conversation chatbot

```bash
curl -X POST http://localhost:8006/api/chatbot/conversations/ \
  -H "Authorization: Bearer <token_etudiant>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Réponse :**
```json
{
  "id"        : 1,
  "statut"    : "active",
  "date_debut": "2025-01-15T10:30:00Z",
  "messages"  : [{
    "emetteur": "chatbot",
    "contenu" : "Bonjour ! Je suis l'assistant virtuel de l'UADB..."
  }]
}
```

### 4. Envoyer un message au chatbot

```bash
curl -X POST http://localhost:8006/api/chatbot/conversations/1/messages/ \
  -H "Authorization: Bearer <token_etudiant>" \
  -H "Content-Type: application/json" \
  -d '{"contenu": "Quelles pièces fournir pour mon dossier ?"}'
```

**Réponse :**
```json
{
  "message_etudiant": {
    "emetteur": "etudiant",
    "contenu" : "Quelles pièces fournir pour mon dossier ?"
  },
  "reponse_chatbot": {
    "emetteur" : "chatbot",
    "contenu"  : "Les pièces obligatoires pour votre dossier sont :\n• Baccalauréat...",
    "intention": "dossier",
    "confiance": 0.82
  },
  "source": "base_connaissance"
}
```

### 5. Tester le chatbot (admin)

```bash
curl -X POST http://localhost:8006/api/chatbot/tester/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{"message": "comment obtenir mon attestation"}'
```

### 6. Relancer les notifications en échec (admin)

```bash
curl -X POST http://localhost:8006/api/notifications/admin/relancer/ \
  -H "Authorization: Bearer <token_admin>"
```

---

## Fonctionnement du chatbot

### Algorithme de réponse

```
Étudiant envoie un message
        ↓
MoteurChatbot.traiter_message()
        ↓
1. Détecter salutation → réponse de bienvenue
        ↓
2. Chercher dans BaseConnaissance :
   - Calculer similarité avec chaque question déclencheur
   - Bonus si mots-clés présents
   - Seuil de confiance : 0.45
        ↓
3. Si score ≥ 0.45 → répondre avec le contenu de l'entrée
        ↓
4. Sinon → détecter intention générale (mots-clés)
        ↓
5. Réponse par défaut avec contacts scolarité
```

### Enrichir la base de connaissance

Via l'interface admin Django ou l'API :

```bash
curl -X POST http://localhost:8006/api/chatbot/base-connaissance/ \
  -H "Authorization: Bearer <token_admin>" \
  -H "Content-Type: application/json" \
  -d '{
    "titre"    : "Nouvelle question",
    "categorie": "inscription",
    "priorite" : 5,
    "questions": "ma question 1\nma question 2\nma question 3",
    "mots_cles": "mot1, mot2, mot3",
    "contenu"  : "La réponse complète du chatbot.",
    "actif"    : true
  }'
```

---

## Tables PostgreSQL créées

| Table | Description |
|-------|-------------|
| `notification.notification` | Toutes les notifications envoyées |
| `notification.conversation` | Sessions de chat avec le chatbot |
| `notification.message` | Messages des conversations |
| `notification.base_connaissance` | Base de connaissances du chatbot (8 entrées initiales) |

---

## Entrées initiales de la base de connaissance

| Catégorie | Titre |
|-----------|-------|
| inscription | Comment s'inscrire à l'UADB ? |
| dossier | Quelles pièces fournir pour le dossier ? |
| deliberation | Comment consulter mes résultats ? |
| attestation | Comment obtenir une attestation ? |
| paiement | Comment payer les frais de scolarité ? |
| contact | Contacts de la scolarité |
| dossier | Suivi de mon dossier |
| calendrier | Quand se déroule la rentrée universitaire ? |

---

## Configuration email Gmail

Pour utiliser Gmail comme serveur SMTP :

1. Activez la validation en 2 étapes sur votre compte Google
2. Générez un "Mot de passe d'application" dans les paramètres de sécurité
3. Utilisez ce mot de passe dans `EMAIL_HOST_PASSWORD`

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # mot de passe d'application
```
