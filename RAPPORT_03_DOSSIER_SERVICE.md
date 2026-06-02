# Service Dossier — dossier_service

## 1. Présentation

Le service dossier gère deux responsabilités majeures :
1. Le **référentiel des formations** proposées par l'UADB (Licences, Masters, Doctorats avec leurs Unités d'Enseignement)
2. Le **dossier étudiant** comprenant les pièces justificatives déposées et leur vérification

Ce service est référencé par tous les autres microservices pour obtenir les informations de formation.

- **Port** : 8003
- **Préfixe URL** : `/api/`
- **Base de données** : `uadb_dossier` (schéma `dossier`)
- **Stockage fichiers** : MinIO (stockage objet)
- **Dépendances** : auth_service (JWT), notification_service, audit_service

---

## 2. Modèles de Données

### 2.1 Modèle `Formation`

Référentiel des formations de l'université, référencé par tous les autres services.

| Champ | Type | Description |
|-------|------|-------------|
| `code_formation` | CharField(20) | Code unique ex. `L3-INFO`, `M1-SI` |
| `libelle` | CharField(150) | Intitulé complet de la formation |
| `niveau` | CharField | `L1`, `L2`, `L3`, `M1`, `M2`, `Doctorat` |
| `specialite` | CharField(100) | Spécialité (ex. Informatique) |
| `departement` | CharField(100) | Département de rattachement |
| `credits_total` | IntegerField | Nombre de crédits total (défaut : 60) |
| `duree_semestres` | IntegerField | Durée en semestres (défaut : 2) |
| `actif` | BooleanField | Formation ouverte aux inscriptions |
| `date_creation` | DateTimeField | Date de création automatique |

---

### 2.2 Modèle `UniteEnseignement`

Programme pédagogique d'une formation. Référencé par les notes de délibération.

| Champ | Type | Description |
|-------|------|-------------|
| `formation` | ForeignKey(Formation) | Formation parente |
| `code_ue` | CharField(20) | Code unique ex. `INF301`, `SI401` |
| `libelle_ue` | CharField(150) | Intitulé de l'UE |
| `semestre` | IntegerField | Numéro du semestre (1 à 4) |
| `credit` | IntegerField | Nombre de crédits (défaut : 3) |
| `coefficient` | DecimalField | Coefficient pour le calcul de moyenne |
| `type_ue` | CharField | `obligatoire`, `optionnel`, `libre` |
| `volume_horaire` | IntegerField | Heures totales d'enseignement |
| `actif` | BooleanField | UE dispensée ou non |

**Contrainte** : `unique_together ('formation', 'code_ue')`

---

### 2.3 Modèle `DossierEtudiant`

Un dossier par étudiant par année universitaire. Le score de complétude est calculé automatiquement selon les pièces déposées et validées.

| Champ | Type | Description |
|-------|------|-------------|
| `etudiant_id` | IntegerField | ID de l'étudiant dans auth_service |
| `formation` | ForeignKey(Formation) | Formation demandée |
| `annee_universitaire` | CharField | Ex. `2024-2025` |
| `etat_dossier` | CharField | `en_cours`, `incomplet`, `complet`, `valide`, `rejete` |
| `score_completude` | IntegerField | Score de 0 à 100 calculé automatiquement |
| `date_creation` | DateField | Date de création automatique |
| `date_validation` | DateField | Date de validation par un agent |
| `valide_par` | IntegerField | ID de l'agent validateur |
| `observation` | TextField | Remarques libres |

**Contrainte** : `unique_together ('etudiant_id', 'annee_universitaire')`

**Propriétés calculées** :
- `est_complet` → vrai si `score_completude == 100`
- `nb_pieces_deposees` → nombre de pièces en attente ou validées
- `nb_pieces_validees` → nombre de pièces validées uniquement

---

### 2.4 Modèle `PieceJustificative`

Chaque fichier déposé dans le dossier est une pièce justificative. Les fichiers sont stockés dans **MinIO**, seul le chemin est enregistré en base.

| Champ | Type | Description |
|-------|------|-------------|
| `dossier` | ForeignKey(DossierEtudiant) | Dossier parent |
| `type_piece` | CharField | `bac`, `cni`, `photo`, `diplome`, `releve_notes`, `acte_naissance`, `autre` |
| `nom_fichier` | CharField(255) | Nom original du fichier |
| `chemin_stockage` | CharField(500) | Chemin MinIO : `dossiers/{etudiant_id}/{type}/{uuid}.pdf` |
| `taille_fichier` | IntegerField | Taille en octets |
| `type_mime` | CharField | `application/pdf`, `image/jpeg`, `image/png` |
| `statut_verification` | CharField | `en_attente`, `valide`, `rejete`, `expire` |
| `verifie_par` | IntegerField | ID de l'agent vérificateur |
| `date_upload` | DateTimeField | Date du dépôt automatique |
| `date_verification` | DateTimeField | Date de vérification |
| `motif_rejet` | TextField | Motif si la pièce est rejetée |

---

## 3. Calcul du Score de Complétude

Le score de complétude (0 à 100) est calculé automatiquement à chaque fois qu'une pièce est ajoutée ou validée :

```
Pièces obligatoires définies par le système :
  - Baccalauréat
  - Carte Nationale d'Identité
  - Photo d'identité
  - Acte de naissance

score = (nb_pièces_validées / nb_pièces_obligatoires) × 100
```

Lorsque `score_completude == 100`, une notification est envoyée à l'étudiant et au service inscription pour débloquer la suite du workflow.

---

## 4. Endpoints de l'API

### 4.1 Formations

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/formations/` | Authentifié | Lister toutes les formations actives |
| `POST` | `/api/formations/` | Admin | Créer une nouvelle formation |
| `GET` | `/api/formations/{pk}/` | Authentifié | Détail d'une formation |
| `PATCH/PUT` | `/api/formations/{pk}/` | Admin | Modifier une formation |
| `DELETE` | `/api/formations/{pk}/` | Admin | Supprimer une formation |
| `GET` | `/api/formations/{pk}/ues/` | Authentifié | Unités d'enseignement d'une formation |

### 4.2 Dossier Étudiant

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `GET` | `/api/dossiers/mon-dossier/` | Étudiant | Consulter son dossier de l'année en cours |
| `POST` | `/api/dossiers/` | Étudiant | Créer un nouveau dossier |
| `GET` | `/api/dossiers/{pk}/` | Étudiant/Agent | Détail d'un dossier |
| `GET` | `/api/dossiers/liste/` | Agent/Admin | Lister tous les dossiers |
| `POST` | `/api/dossiers/{pk}/valider/` | Agent Scolarité | Valider le dossier |
| `POST` | `/api/dossiers/{pk}/rejeter/` | Agent Scolarité | Rejeter le dossier |

### 4.3 Pièces Justificatives

| Méthode | URL | Accès | Description |
|---------|-----|-------|-------------|
| `POST` | `/api/dossiers/{pk}/pieces/` | Étudiant | Déposer une pièce justificative |
| `GET` | `/api/dossiers/{pk}/pieces/` | Étudiant/Agent | Lister les pièces d'un dossier |
| `GET` | `/api/pieces/{pk}/` | Étudiant/Agent | Détail et téléchargement d'une pièce |
| `POST` | `/api/pieces/{pk}/verifier/` | Agent Scolarité | Valider ou rejeter une pièce |
| `DELETE` | `/api/pieces/{pk}/` | Étudiant | Supprimer une pièce non encore vérifiée |

---

## 5. Stockage MinIO

L'organisation des fichiers dans MinIO suit la convention :

```
Bucket : uadb-dossiers
├── dossiers/
│   ├── {etudiant_id}/
│   │   ├── bac/
│   │   │   └── {uuid}.pdf
│   │   ├── cni/
│   │   │   └── {uuid}.jpg
│   │   └── photo/
│   │       └── {uuid}.jpg
```

- L'accès aux fichiers se fait via une **URL signée** avec durée de validité limitée
- Aucune URL publique permanente n'est exposée

---

## 6. Notifications Automatiques

| Événement | Action |
|-----------|--------|
| Pièce déposée | Notification à l'agent scolarité |
| Pièce validée | Email à l'étudiant |
| Pièce rejetée | Email à l'étudiant avec motif |
| Dossier complet (score = 100) | Email à l'étudiant + signal au service inscription |
| Dossier validé par l'agent | Email de confirmation à l'étudiant |

---

## 7. Rôle Central du Service

Le `dossier_service` est le **référentiel des formations** pour tout le système :
- L'`inscription_service` appelle `/api/formations/{id}/` pour calculer les frais
- Le `deliberation_service` appelle `/api/formations/{id}/ues/` pour les unités d'enseignement
- L'`attestation_service` appelle ce service pour vérifier la formation de l'étudiant
