# Service Attestation — attestation_service

## 1. Présentation

Le service attestation gère l'ensemble du cycle de vie des documents officiels demandés par les étudiants : de la soumission de la demande jusqu'à la génération du PDF signé et son stockage sécurisé. Le traitement est **partiellement automatisé** grâce au moteur de règles du service IA.

- **Port** : 8007
- **Préfixe URL** : `/api/`
- **Base de données** : `uadb_attestation` (schéma `attestation`)
- **Génération PDF** : ReportLab (bibliothèque Python)
- **Stockage** : MinIO
- **Dépendances** : auth_service, inscription_service, deliberation_service, ia_service, notification_service, audit_service

---

## 2. Modèles de Données

### 2.1 Modèle `DemandeAttestation`

Soumise par l'étudiant, traitée automatiquement par le moteur de règles du service IA.

| Champ | Type | Description |
|-------|------|-------------|
| `etudiant_id` | IntegerField | ID de l'étudiant dans auth_service |
| `type_attestation` | CharField | Type du document demandé |
| `annee_universitaire` | CharField | Année concernée (ex. `2024-2025`) |
| `motif` | TextField | Raison de la demande : bourse, stage, concours... |
| `statut` | CharField | `en_attente`, `approuvee`, `refusee`, `generee` |
| `decision_ia` | CharField | `eligible` ou `non_eligible` — résultat du moteur IA |
| `motif_refus` | TextField | Motif automatique ou manuel du refus |
| `inscription_id` | IntegerField | Référence à l'inscription concernée |
| `deliberation_id` | IntegerField | Référence à la délibération concernée |
| `date_demande` | DateTimeField | Date de soumission automatique |
| `date_traitement` | DateTimeField | Date de traitement |
| `traite_par` | IntegerField | ID de l'agent — NULL si traitement automatique |

**Types d'attestation disponibles** :

| Code | Libellé | Condition d'éligibilité |
|------|---------|-------------------------|
| `inscription` | Attestation d'inscription | Inscription validée pour l'année demandée |
| `passage` | Attestation de passage | Résultat = `admis` ou `rattrapage` pour passer en niveau supérieur |
| `reussite` | Attestation de réussite | Résultat = `admis` avec moyenne ≥ 10 |
| `releve_notes` | Relevé de notes | Délibération clôturée pour l'année demandée |
| `scolarite` | Certificat de scolarité | Inscription en cours pour l'année en cours |

---

### 2.2 Modèle `Attestation`

Générée automatiquement après approbation. Contient le fichier PDF et le code de vérification unique.

| Champ | Type | Description |
|-------|------|-------------|
| `demande` | OneToOneField(DemandeAttestation) | Demande parente |
| `numero_attestation` | CharField | Numéro officiel unique (UUID) |
| `code_verification` | CharField | Code unique pour vérification publique |
| `chemin_fichier` | CharField | Chemin MinIO du PDF généré |
| `statut` | CharField | `generee`, `delivree`, `annulee` |
| `date_generation` | DateTimeField | Date de génération automatique |
| `date_delivrance` | DateTimeField | Date de remise à l'étudiant |
| `nb_telechargements` | IntegerField | Compteur de téléchargements |
| `signature_numerique` | TextField | Empreinte cryptographique du document |

---

## 3. Processus de Traitement

```
1. SOUMISSION        → L'étudiant soumet sa demande
   ↓
2. VÉRIFICATION IA   → ia_service évalue l'éligibilité :
                        - L'étudiant est-il inscrit ?
                        - A-t-il les résultats nécessaires ?
                        - La délibération est-elle clôturée ?
   ↓
3a. NON ÉLIGIBLE     → statut = "refusee" + notification à l'étudiant
                        avec motif détaillé

3b. ÉLIGIBLE         → statut = "approuvee"
   ↓
4. GÉNÉRATION PDF    → ReportLab génère le document officiel :
                        - En-tête UADB
                        - Données de l'étudiant
                        - Informations académiques
                        - QR Code avec le code_verification
                        - Signature numérique
   ↓
5. STOCKAGE          → PDF stocké sur MinIO
   ↓
6. NOTIFICATION      → Email à l'étudiant avec lien de téléchargement
   statut = "generee"
```

---

## 4. Endpoints de l'API

### 4.1 Côté Étudiant

| Méthode | URL | Description |
|---------|-----|-------------|
| `POST` | `/api/attestations/demandes/` | Soumettre une demande d'attestation |
| `GET` | `/api/attestations/mes-demandes/` | Lister toutes ses demandes |
| `GET` | `/api/attestations/demandes/{pk}/` | Détail d'une demande |
| `GET` | `/api/attestations/{pk}/telecharger/` | Télécharger le PDF de l'attestation |
| `POST` | `/api/attestations/demandes/{pk}/regenerer/` | Régénérer un PDF (si endommagé) |

**Exemple de requête POST /api/attestations/demandes/ :**
```json
{
  "type_attestation": "inscription",
  "annee_universitaire": "2024-2025",
  "motif": "Demande de bourse universitaire"
}
```

### 4.2 Vérification Publique (sans authentification)

| Méthode | URL | Description |
|---------|-----|-------------|
| `GET` | `/api/attestations/verifier/{code}/` | Vérifier l'authenticité d'une attestation |

Cet endpoint permet à **n'importe qui** (université partenaire, employeur, etc.) de vérifier qu'une attestation est authentique en utilisant le code imprimé sur le document.

**Réponse si valide** :
```json
{
  "valide": true,
  "etudiant": "DIALLO Mamadou",
  "type": "Attestation d'inscription",
  "annee": "2024-2025",
  "date_generation": "2025-01-15",
  "statut": "generee"
}
```

### 4.3 Administration

| Méthode | URL | Description |
|---------|-----|-------------|
| `GET` | `/api/attestations/admin/demandes/` | Lister toutes les demandes |
| `GET/PATCH` | `/api/attestations/admin/demandes/{pk}/` | Détail et traitement manuel |
| `GET` | `/api/attestations/statistiques/` | Statistiques par type et période |

---

## 5. Génération du PDF

Le PDF est généré avec **ReportLab** et comprend :

| Élément | Description |
|---------|-------------|
| En-tête | Logo UADB + intitulé officiel du document |
| Identification | Nom, prénom, matricule, date de naissance |
| Formation | Intitulé, niveau, année universitaire |
| Corps | Contenu selon le type (mention, moyennes, notes...) |
| QR Code | Code de vérification pour authentification rapide |
| Pied de page | Numéro d'attestation, date, signature du directeur |

---

## 6. Sécurité et Authenticité

- Chaque attestation possède un **code de vérification unique** (UUID)
- Un **QR Code** imprimé sur le document pointe vers l'URL de vérification publique
- La **signature numérique** (hash SHA-256) garantit l'intégrité du fichier
- Les téléchargements sont tracés (compteur + audit)
- Le fichier PDF n'est **jamais accessible directement** via MinIO — il passe obligatoirement par le service

---

## 7. Traçabilité

| Action | Code Audit |
|--------|-----------|
| Soumission de demande | `SUBMIT` |
| Décision automatique IA | `DECISION_AUTO` |
| Génération du PDF | `GENERATE` |
| Téléchargement | `DOWNLOAD` |
| Vérification publique | `VERIFY` |
