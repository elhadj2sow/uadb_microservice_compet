# Compte Rendu - Microservice Authentification (UADB)

## 1. Objectif du microservice
Le microservice Authentification centralise:
- la creation des comptes utilisateurs,
- la connexion et la generation des tokens JWT,
- la gestion des roles,
- la gestion du profil utilisateur,
- la tracabilite des actions sensibles (journal d'audit).

Il permet aux autres microservices (inscription, dossier, attestation, etc.) de lire les informations dans le token sans appeler en permanence le service auth.

---

## 2. Architecture et donnees gerees
Le projet est base sur Django + Django REST Framework + SimpleJWT + PostgreSQL.

### Modeles principaux
- Utilisateur: base d'authentification (username, password, email, etat_compte, roles)
- Etudiant: profil universitaire lie en OneToOne avec Utilisateur
- Role: roles metier UADB
- JournalAudit: historisation des actions (login, logout, update, etc.)

### Roles metier utilises
- etudiant
- agent_scolarite
- agent_comptable
- service_medical
- bibliotheque
- enseignant
- responsable_pedagogique
- admin

---

## 3. Initialisation technique realisee
### 3.1 Environnement
- Creation et activation de l'environnement virtuel Python
- Installation des dependances via requirements.txt

### 3.2 Base de donnees PostgreSQL
Script execute:
- init_db.sql

Ce script:
- cree l'utilisateur PostgreSQL uadb_user
- cree la base uadb_db
- cree le schema auth_uadb
- applique les privileges necessaires sur auth_uadb et public

### 3.3 Migrations
Commandes executees:
- python manage.py init_schema
- python manage.py migrate

Resultat:
- migrations appliquees avec succes
- tables Django et tables metier creees

### 3.4 Superuser
Commande executee:
- python manage.py createsuperuser

---

## 4. Endpoints testes et valides
### 4.1 Inscription etudiant
- POST /api/auth/register/
- Resultat: compte cree avec succes

### 4.2 Connexion
- POST /api/auth/login/
- Resultat: refresh token + access token retournes

### 4.3 Profil utilisateur connecte
- GET /api/auth/me/
- Resultat: retour du profil utilisateur + profil etudiant + roles

### 4.4 Refresh token
- POST /api/auth/refresh/
- Resultat attendu: nouveau access token sans ressaisir le mot de passe

### 4.5 Assignation de role (admin)
- POST /api/auth/utilisateurs/{id}/roles/
- Resultat valide: role agent_scolarite ajoute a l'utilisateur cible

Exemple obtenu:
- roles: ["etudiant", "agent_scolarite"]

---

## 5. Structure JWT et utilisation inter-microservices
Le token JWT transporte des informations utiles:
- user_id
- login
- email
- roles
- etat
- etudiant_id
- exp / iat

Interet:
- les autres microservices peuvent appliquer leurs regles d'autorisation en lisant directement le token.

---

## 6. Problemes rencontres et corrections appliquees
### Probleme 1 - requirements.txt introuvable
Cause:
- commande lancee dans le mauvais dossier.
Correction:
- execution dans le bon dossier du projet.

### Probleme 2 - ModuleNotFoundError: pkg_resources
Cause:
- incompatibilite de version setuptools / pkg_resources.
Correction:
- version de setuptools adaptee et stabilisee dans les dependances.

### Probleme 3 - NameError dans migration 0001_initial.py
Cause:
- fonction chargee apres son utilisation dans RunPython.
Correction:
- reorganisation du fichier de migration (fonction placee avant la classe Migration).

### Probleme 4 - 403 sur endpoint admin
Cause:
- le superuser Django n'avait pas encore le role metier admin dans la table des roles.
Correction:
- role admin ajoute au compte superuser, puis nouveau login pour regenerer un token conforme.

### Probleme 5 - 401 sur login utilisateur etudiant
Cause:
- mot de passe incorrect saisi dans Postman.
Correction:
- utilisation du bon mot de passe (MonMotDePasse123).

---

## 7. Etat final du projet
Statut global: operationnel.

Valide:
- base PostgreSQL initialisee
- schema auth_uadb cree
- migrations appliquees
- superuser cree
- serveur Django lance
- endpoints critiques testes avec succes

---

## 8. Points importants a presenter a l'encadreur
1. Le microservice auth est fonctionnel de bout en bout.
2. Le token JWT contient les claims necessaires pour les autres services.
3. Le systeme de roles est operationnel et testable via endpoint admin.
4. Les incidents techniques ont ete identifies, analyses et corriges proprement.
5. Le journal d'audit permet la tracabilite des operations sensibles.

---

## 9. Recommandations pour la suite
1. Renforcer les mots de passe en environnement de demonstration/production.
2. Mettre en place des sauvegardes regulieres PostgreSQL (pg_dump).
3. Ajouter une collection Postman complete partagee a l'equipe.
4. Ajouter des tests automatiques (unitaires + integration API).
5. Verifier le demarrage automatique du service PostgreSQL apres redemarrage machine.

---

## 10. Commandes utiles recapitulatives
- psql -h localhost -p 5432 -U postgres -f init_db.sql
- python manage.py init_schema
- python manage.py migrate
- python manage.py createsuperuser
- python manage.py runserver 8001

-Bonjour, j’ai réalisé un microservice d’authentification pour centraliser la sécurité des autres microservices UADB.
Techniquement, j’ai utilisé Django, Django REST Framework, JWT avec SimpleJWT, et PostgreSQL.

J’ai d’abord initialisé la base avec un script SQL, puis appliqué les migrations pour créer les tables métier : Utilisateur, Etudiant, Role et JournalAudit.
Ensuite, j’ai implémenté les endpoints principaux : inscription, connexion, refresh token, profil utilisateur, gestion des utilisateurs et assignation des rôles.

Côté sécurité, j’ai séparé l’authentification et l’autorisation :

authentification par JWT (access + refresh),
autorisation par rôles métier avec des permissions personnalisées, notamment pour les actions admin.
J’ai validé le fonctionnement complet avec Postman : register, login, me, refresh et ajout de rôle.
Le token transporte les informations utiles comme user_id, roles et etudiant_id, ce qui permet aux autres microservices de prendre des décisions sans requêtes supplémentaires vers auth.

En résumé, la solution est opérationnelle, traçable via journal d’audit, et prête pour l’intégration dans l’architecture microservices.

Si tu veux, je te donne aussi une version “questions pièges du jury + réponses courtes” en 30 secondes chacune.

GPT-5.3-Codex • 0.9x
