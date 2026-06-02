# Service Notification — notification_service

## 1. Présentation

Le service notification est le **hub central de communication** du système UADB. Il reçoit des demandes d'envoi de notifications depuis tous les autres microservices et gère leur distribution par email, SMS ou canal interne. Il intègre également un **chatbot** pour répondre aux questions fréquentes des étudiants.

- **Port** : 8006
- **Préfixe URL** : `/api/`
- **Base de données** : `uadb_notification` (schéma `notification`)
- **Dépendances** : auth_service (JWT + profil étudiant)
- **Serveur email** : SMTP configuré (ex. Gmail, SendGrid)

---

## 2. Modèles de Données

### 2.1 Modèle `Notification`

Trace chaque notification envoyée ou planifiée.

| Champ | Type | Description |
|-------|------|-------------|
| `etudiant_id` | IntegerField | ID étudiant destinataire dans auth_service |
| `service_destinataire` | CharField | Service destinataire : `scolarite`, `comptabilite`, `medical`, `bibliotheque` |
| `type_notification` | CharField | `inscription`, `dossier`, `deliberation`, `attestation`, `workflow`, `paiement`, `systeme`, `chatbot` |
| `canal` | CharField | `email`, `sms`, `interne`, `push` |
| `sujet` | CharField(200) | Objet de l'email |
| `message` | TextField | Corps du message |
| `inscription_id` | IntegerField | Référence à une inscription (optionnel) |
| `dossier_id` | IntegerField | Référence à un dossier (optionnel) |
| `deliberation_id` | IntegerField | Référence à une délibération (optionnel) |
| `attestation_id` | IntegerField | Référence à une attestation (optionnel) |
| `statut_envoi` | CharField | `en_attente`, `envoye`, `echec`, `lu` |
| `date_notification` | DateTimeField | Horodatage automatique |
| `date_envoi` | DateTimeField | Date d'envoi effectif |
| `date_lecture` | DateTimeField | Date de lecture par le destinataire |
| `erreur` | TextField | Message d'erreur si envoi échoué |
| `emetteur_service` | CharField | Service qui a déclenché la notification |
| `nb_tentatives` | IntegerField | Nombre de tentatives d'envoi |

---

### 2.2 Modèle `ConversationChatbot`

Représente une session de conversation entre un étudiant et le chatbot.

| Champ | Type | Description |
|-------|------|-------------|
| `etudiant_id` | IntegerField | ID de l'étudiant |
| `date_debut` | DateTimeField | Début de la session |
| `date_fin` | DateTimeField | Fin de la session (nullable) |
| `statut` | CharField | `active`, `terminee` |

---

### 2.3 Modèle `MessageChatbot`

Chaque échange (question ou réponse) dans une conversation.

| Champ | Type | Description |
|-------|------|-------------|
| `conversation` | ForeignKey(Conversation) | Session parente |
| `auteur` | CharField | `etudiant` ou `bot` |
| `contenu` | TextField | Texte du message |
| `date_message` | DateTimeField | Horodatage automatique |
| `intention` | CharField | Intention détectée (ex. `statut_inscription`) |

---

### 2.4 Modèle `BaseConnaissance`

Base de données des réponses automatiques du chatbot.

| Champ | Type | Description |
|-------|------|-------------|
| `question` | TextField | Question de référence |
| `reponse` | TextField | Réponse associée |
| `mots_cles` | JSONField | Liste de mots-clés déclencheurs |
| `categorie` | CharField | Catégorie : `inscription`, `dossier`, `resultats`, etc. |
| `actif` | BooleanField | Entrée active ou non |

---

## 3. Mécanisme d'Envoi

### 3.1 Processus Standard

```
Service X  ──POST──►  /api/notifications/  ──►  Notification créée en base
                                                      │
                                               (traitement immédiat)
                                                      │
                                          ┌───────────▼───────────┐
                                          │  Résolution email     │
                                          │  (appel auth_service) │
                                          └───────────┬───────────┘
                                                      │
                                          ┌───────────▼───────────┐
                                          │   Envoi SMTP          │
                                          │   statut = "envoye"   │
                                          └───────────────────────┘
```

### 3.2 Gestion des Échecs

- En cas d'échec SMTP, `statut_envoi = "echec"` et le message d'erreur est enregistré
- L'endpoint `/api/notifications/admin/relancer/` permet de **relancer les envois échoués**
- Le compteur `nb_tentatives` est incrémenté à chaque tentative

---

## 4. Endpoints de l'API

### 4.1 Envoi de Notifications (appelé par les autres services)

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `POST` | `/api/notifications/` | Service interne | Envoyer une notification |

**Exemple de corps de requête** :
```json
{
  "etudiant_id": 42,
  "type_notification": "inscription",
  "canal": "email",
  "sujet": "Votre inscription a été validée",
  "message": "Félicitations ! Votre inscription pour 2024-2025 est confirmée. Votre matricule : 2024-L1-0042.",
  "inscription_id": 15,
  "emetteur_service": "inscription_service"
}
```

### 4.2 Côté Étudiant

| Méthode | URL | Description |
|---------|-----|-------------|
| `GET` | `/api/notifications/mes-notifications/` | Lister ses notifications (paginées) |
| `POST` | `/api/notifications/{pk}/lire/` | Marquer une notification comme lue |
| `POST` | `/api/notifications/tout-lire/` | Marquer toutes ses notifications comme lues |

### 4.3 Administration

| Méthode | URL | Description |
|---------|-----|-------------|
| `GET` | `/api/notifications/admin/` | Lister toutes les notifications (filtrables) |
| `POST` | `/api/notifications/admin/relancer/` | Relancer les envois échoués |
| `GET` | `/api/notifications/statistiques/` | Statistiques d'envoi par période |

### 4.4 Chatbot

| Méthode | URL | Description |
|---------|-----|-------------|
| `POST` | `/api/chatbot/conversations/` | Démarrer une nouvelle conversation |
| `GET` | `/api/chatbot/conversations/mes-conversations/` | Lister ses conversations |
| `GET` | `/api/chatbot/conversations/{pk}/` | Détail d'une conversation |
| `POST` | `/api/chatbot/conversations/{pk}/messages/` | Envoyer un message |
| `GET` | `/api/chatbot/base-connaissance/` | Consulter la base de connaissance |
| `POST` | `/api/chatbot/tester/` | Tester une question (admin) |

---

## 5. Chatbot — Fonctionnement

Le chatbot répond aux questions fréquentes des étudiants en utilisant une base de connaissance interne :

1. L'étudiant envoie un message
2. Le système analyse les **mots-clés** du message
3. La réponse la plus proche dans `BaseConnaissance` est retournée
4. Si aucune correspondance : message par défaut invitant à contacter la scolarité

**Catégories de questions gérées** :
- Statut d'inscription et documents nécessaires
- Délais et dates importantes
- Frais d'inscription et modes de paiement
- Résultats et délibérations
- Attestations et relevés de notes

---

## 6. Notifications Envoyées par Service

| Service émetteur | Événement | Message envoyé |
|------------------|-----------|----------------|
| inscription_service | Préinscription reçue | Confirmation avec numéro provisoire |
| inscription_service | Inscription validée | Confirmation avec matricule définitif |
| inscription_service | Étape rejetée | Motif du rejet |
| dossier_service | Dossier complet (100%) | Invitation à finaliser l'inscription |
| dossier_service | Pièce rejetée | Motif du rejet, invitation à déposer à nouveau |
| deliberation_service | Résultats publiés | Décision et moyenne |
| attestation_service | Attestation générée | Lien de téléchargement |

---

## 7. Point Technique Important

Lors de la résolution de l'adresse email d'un destinataire, le service fait appel à `auth_service` en utilisant l'`etudiant_id`. Il est important de noter que l'`etudiant_id` (ID du profil étudiant) peut **différer** de l'`utilisateur_id` (ID du compte) — le service vérifie le mapping avant d'utiliser l'email.
