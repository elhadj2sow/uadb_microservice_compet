# 📋 Scénario de Test Complet - API Dossier Service (Postman)

## 🚀 Préparation

**Serveurs actifs :**
- ✅ Auth Service: `http://localhost:8001`
- ✅ Dossier Service: `http://localhost:8003`
- ✅ MinIO: `http://localhost:9000` (stockage fichiers)
- ✅ PostgreSQL: Bases uadb_db et uadb2_db

---

## 📌 ÉTAPE 1 : Obtenir le Token Étudiant

**Requête :**
```
POST http://localhost:8001/api/auth/login/
Content-Type: application/json
```

**Body (JSON) :**
```json
{
  "username": "etudiant1",
  "password": "etudiant1_pass"
}
```

**Réponse attendue (200 OK) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 3,
    "username": "etudiant1",
    "email": "etudiant1@uadb.edu",
    "roles": ["etudiant"]
  }
}
```

**⚠️ ACTION :** 
- ✅ Copier le token `access` 
- 🔧 Dans Postman, créer une **Collection Variable** nommée `token_etudiant` avec cette valeur

---

## 📌 ÉTAPE 2 : Lister les Formations Disponibles

**Requête :**
```
GET http://localhost:8003/api/formations/
Authorization: Bearer {{token_etudiant}}
```

**Réponse attendue (200 OK) :**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "code_formation": "L3-INFO",
      "libelle": "Licence 3 Informatique",
      "niveau": "L3",
      "actif": true
    },
    {
      "id": 2,
      "code_formation": "M1-SI",
      "libelle": "Master 1 Systèmes d'Information",
      "niveau": "M1",
      "actif": true
    },
    {
      "id": 3,
      "code_formation": "M2-SI",
      "libelle": "Master 2 Systèmes d'Information",
      "niveau": "M2",
      "actif": true
    },
    {
      "id": 4,
      "code_formation": "M1-SR",
      "libelle": "Master 1 Systèmes et Réseaux",
      "niveau": "M1",
      "actif": true
    },
    {
      "id": 5,
      "code_formation": "M2-SR",
      "libelle": "Master 2 Systèmes et Réseaux",
      "niveau": "M2",
      "actif": true
    }
  ]
}
```

**⚠️ ACTION :**
- ✅ Noter l'ID d'une formation (ex: `2` pour M1-SI)
- 🔧 Créer une **Collection Variable** `formation_id = 2`

---

## 📌 ÉTAPE 3 : Créer un Dossier pour l'Étudiant

**Requête :**
```
POST http://localhost:8003/api/dossiers/
Authorization: Bearer {{token_etudiant}}
Content-Type: application/json
```

**Body (JSON) :**
```json
{
  "formation": 2,
  "annee_universitaire": "2024-2025"
}
```

**Réponse attendue (201 Created) :**
```json
{
  "id": 1,
  "etudiant_id": 3,
  "formation": 2,
  "formation_detail": {
    "id": 2,
    "code_formation": "M1-SI",
    "libelle": "Master 1 Systèmes d'Information",
    "niveau": "M1"
  },
  "annee_universitaire": "2024-2025",
  "etat_dossier": "en_cours",
  "score_completude": 0,
  "pieces": [],
  "pieces_manquantes": [
    "bac",
    "cni",
    "photo",
    "acte_naissance",
    "certificat_medical",
    "quitus_bibliotheque",
    "recu_paiement"
  ],
  "pieces_expirees": []
}
```

**⚠️ ACTION :**
- ✅ Copier l'ID du dossier créé (ex: `1`)
- 🔧 Créer une **Collection Variable** `dossier_id = 1`

---

## 📌 ÉTAPE 4 : Déposer une Pièce Justificative (Baccalauréat)

**Requête :**
```
POST http://localhost:8003/api/dossiers/1/pieces/
Authorization: Bearer {{token_etudiant}}
Content-Type: multipart/form-data
```

**Form Data (multipart) :**
```
type_piece: bac
fichier: [Sélectionner un fichier PDF/PNG/JPG]
est_obligatoire: true
```

**Réponse attendue (201 Created) :**
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
  "url_telechargement": "http://localhost:9000/uadb-dossiers/dossier_1/bac_..."
}
```

**📝 Note :** 
- Vous pouvez créer un fichier test avec `echo "test" > test.pdf` ou utiliser un vrai PDF
- Pour les prochaines pièces, changez simplement `type_piece` à : `cni`, `photo`, `acte_naissance`, `certificat_medical`, `quitus_bibliotheque`, `recu_paiement`

**⚠️ ACTION :**
- 🔧 Créer une **Collection Variable** `piece_id = 1`

---

## 📌 ÉTAPE 5 : Consulter le Dossier (Score Avant Validation)

**Requête :**
```
GET http://localhost:8003/api/dossiers/1/
Authorization: Bearer {{token_etudiant}}
```

**Réponse attendue (200 OK) :**
```json
{
  "id": 1,
  "etudiant_id": 3,
  "formation": 2,
  "annee_universitaire": "2024-2025",
  "etat_dossier": "en_cours",
  "score_completude": 0,
  "pieces": [
    {
      "id": 1,
      "type_piece": "bac",
      "statut_verification": "en_attente",
      "est_obligatoire": true
    }
  ],
  "pieces_manquantes": 6,
  "pieces_expirees": []
}
```

**📊 Analyse :**
- ✅ 1 pièce déposée
- ⏳ Statut: `en_attente` (agent doit valider)
- 📈 Score: `0` (pas de pièces validées)

---

## 📌 ÉTAPE 6 : Recommencer l'ÉTAPE 4 pour les 6 pièces manquantes

**Déposer les pièces suivantes :** `cni`, `photo`, `acte_naissance`, `certificat_medical`, `quitus_bibliotheque`, `recu_paiement`

Pour chaque pièce :
1. POST `/api/dossiers/1/pieces/`
2. Changer `type_piece` en fonction
3. Sélectionner un fichier différent

Après chaque dépôt, le score reste `0` car les pièces ne sont pas validées.

---

## 📌 ÉTAPE 7 : Obtenir le Token Agent Scolarité

**Requête :**
```
POST http://localhost:8001/api/auth/login/
Content-Type: application/json
```

**Body (JSON) :**
```json
{
  "username": "agent_scolarite1",
  "password": "agent_scolarite1_pass"
}
```

**Réponse attendue (200 OK) :**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "...",
  "user": {
    "id": 4,
    "username": "agent_scolarite1",
    "email": "agent_scolarite1@uadb.edu",
    "roles": ["agent_scolarite"]
  }
}
```

**⚠️ ACTION :**
- 🔧 Créer une **Collection Variable** `token_agent = <access_token>`

---

## 📌 ÉTAPE 8 : Valider la Première Pièce (Agent)

**Requête :**
```
PATCH http://localhost:8003/api/pieces/1/verifier/
Authorization: Bearer {{token_agent}}
Content-Type: application/json
```

**Body (JSON) :**
```json
{
  "action": "valider"
}
```

**Réponse attendue (200 OK) :**
```json
{
  "id": 1,
  "type_piece": "bac",
  "statut_verification": "validee",
  "remarque_validation": null
}
```

**🔄 Signal Automatique :**
- ✅ PieceJustificative.statut_verification → `validee`
- ✅ Signal post_save déclenché
- ✅ recalculer_completude() exécutée
- ✅ DossierEtudiant.score_completude = (1/7) × 100 = **14.29%**

---

## 📌 ÉTAPE 9 : Vérifier le Score Après Validation

**Requête :**
```
GET http://localhost:8003/api/dossiers/1/
Authorization: Bearer {{token_etudiant}}
```

**Réponse attendue (200 OK) :**
```json
{
  "id": 1,
  "etudiant_id": 3,
  "etat_dossier": "en_cours",
  "score_completude": 14.29,
  "pieces": [
    {
      "id": 1,
      "type_piece": "bac",
      "statut_verification": "validee"
    },
    {
      "id": 2,
      "type_piece": "cni",
      "statut_verification": "en_attente"
    },
    ...
  ]
}
```

**📊 Analyse :**
- 📈 Score: **14.29%** (1 pièce validée / 7)
- 🔄 État: `en_cours` (incomplet)

---

## 📌 ÉTAPE 10 : Rejeter une Pièce avec Motif

**Requête :**
```
PATCH http://localhost:8003/api/pieces/2/verifier/
Authorization: Bearer {{token_agent}}
Content-Type: application/json
```

**Body (JSON) :**
```json
{
  "action": "rejeter",
  "motif_rejet": "Document illisible, veuillez uploader une photo plus claire avec fond blanc."
}
```

**Réponse attendue (200 OK) :**
```json
{
  "id": 2,
  "type_piece": "cni",
  "statut_verification": "rejetee",
  "motif_rejet": "Document illisible, veuillez uploader une photo plus claire avec fond blanc."
}
```

---

## 📌 ÉTAPE 11 : Valider les 6 Pièces Restantes

**Requête :** (répéter pour pieces 3, 4, 5, 6, 7)
```
PATCH http://localhost:8003/api/pieces/{id}/verifier/
Authorization: Bearer {{token_agent}}
Content-Type: application/json
```

**Body (JSON) :**
```json
{
  "action": "valider"
}
```

Après chaque validation :
- Score augmente de 14.29%
- Après la 7ème validation → **Score = 100%** 🎉

---

## 📌 ÉTAPE 12 : Consulter le Score Final (100%)

**Requête :**
```
GET http://localhost:8003/api/dossiers/1/
Authorization: Bearer {{token_etudiant}}
```

**Réponse attendue (200 OK) :**
```json
{
  "id": 1,
  "etudiant_id": 3,
  "etat_dossier": "complet",
  "score_completude": 100,
  "pieces": [
    {
      "id": 1,
      "type_piece": "bac",
      "statut_verification": "validee"
    },
    {
      "id": 2,
      "type_piece": "cni",
      "statut_verification": "validee"
    },
    ...
    {
      "id": 7,
      "type_piece": "recu_paiement",
      "statut_verification": "validee"
    }
  ],
  "pieces_manquantes": [],
  "pieces_expirees": []
}
```

**🎉 État Final :**
- ✅ `etat_dossier` = **`complet`**
- ✅ `score_completude` = **`100`**
- 📧 Notification envoyée à l'étudiant
- 🔍 Appel service IA pour traçabilité

---

## 📌 ÉTAPE 13 : Consulter le Tableau de Bord Admin

**Requête :**
```
GET http://localhost:8003/api/dossiers/statistiques/
Authorization: Bearer {{token_admin}}
```

**Réponse attendue (200 OK) :**
```json
{
  "total_dossiers": 1,
  "dossiers_complets": 1,
  "dossiers_en_cours": 0,
  "dossiers_incomplets": 0,
  "score_moyen": 100,
  "statistiques_pieces": {
    "total_pieces": 7,
    "pieces_validees": 7,
    "pieces_rejetees": 0,
    "pieces_en_attente": 0
  }
}
```

---

## 🔐 Guide Authentification Postman

### Variables de Collection à Créer :

```
{{token_etudiant}}        → Token JWT étudiant
{{token_agent}}           → Token JWT agent scolarité
{{token_admin}}           → Token JWT admin
{{formation_id}}          → ID formation (2)
{{dossier_id}}            → ID dossier
{{piece_id}}              → ID pièce
```

### Configuration Headers Automatiques :

Ajouter à chaque requête protégée :
```
Authorization: Bearer {{token_etudiant}}
(ou {{token_agent}}, {{token_admin}} selon le rôle)
```

---

## 📊 Résumé du Flux

```
1. Login Étudiant → Token
2. Lister Formations
3. Créer Dossier
4. Déposer 7 pièces (statut: en_attente)
5. Check Dossier → Score: 0%
6. Login Agent
7. Valider 6 pièces → Score: 85.71%
8. Rejeter 1 pièce → Score: 85.71%
9. Valider la pièce rejetée → Score: 100%
10. Check Admin → Tableau de bord
```

---

## ⚠️ Cas d'Erreur Courants

| Erreur | Cause | Solution |
|--------|-------|----------|
| **401 Unauthorized** | Token expiré/invalide | Refaire étape 1 ou 7 |
| **403 Forbidden** | Rôle insuffisant | Utiliser le bon token |
| **404 Not Found** | Dossier/Pièce inexistante | Vérifier les IDs |
| **400 Bad Request** | Formation n'existe pas | Utiliser formation_id = 1-5 |
| **200 (mais minio error)** | MinIO inaccessible | Vérifier: `docker ps` |

---

## ✅ Checklist Finale

- [ ] Auth Service running (8001)
- [ ] Dossier Service running (8003)
- [ ] MinIO running (9000/9001)
- [ ] PostgreSQL accessible
- [ ] Token étudiant obtenu
- [ ] Dossier créé (id: 1)
- [ ] 7 pièces déposées
- [ ] 7 pièces validées par agent
- [ ] Score = 100%
- [ ] État = "complet"
- [ ] Tableau de bord consulté ✅

