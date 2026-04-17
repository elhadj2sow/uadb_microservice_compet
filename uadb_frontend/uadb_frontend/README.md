# UADB Frontend — Portail Étudiant React

## Technologies

- **React 18** + Vite
- **React Router v6** — navigation
- **Axios** — appels API avec JWT auto-refresh
- **Recharts** — graphiques
- **Lucide React** — icônes
- **React Hot Toast** — notifications

---

## Installation

```bash
cd uadb_frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Architecture des pages

```
src/
├── pages/
│   ├── LoginPage.jsx              ← Connexion
│   ├── etudiant/
│   │   ├── Dashboard.jsx          ← Tableau de bord étudiant
│   │   ├── MonDossier.jsx         ← Dépôt pièces justificatives
│   │   ├── MonInscription.jsx     ← Suivi workflow 4 étapes
│   │   ├── MesResultats.jsx       ← Notes et délibérations
│   │   ├── MesAttestations.jsx    ← Demande et téléchargement PDF
│   │   └── MesNotifications.jsx  ← Centre de notifications
│   ├── agent/
│   │   ├── Dashboard.jsx          ← Stats agents
│   │   ├── GestionDossiers.jsx    ← Valider/rejeter dossiers
│   │   └── GestionInscriptions.jsx ← Valider étapes workflow
│   └── admin/
│       ├── Dashboard.jsx          ← Vue globale + graphiques
│       ├── GestionRegles.jsx      ← CRUD règles IA (sans redéploiement)
│       └── JournalAudit.jsx       ← Consultation journal audit
├── components/
│   ├── layout/Layout.jsx          ← Sidebar + Header
│   └── ui/Chatbot.jsx             ← Chatbot flottant
├── context/AuthContext.jsx        ← JWT + rôles
└── config/api.js                  ← Axios + proxy
```

---

## Comptes de test

| Rôle | Username | Password | Redirection |
|------|----------|----------|-------------|
| Étudiant | etudiant1 | password | `/` |
| Agent scolarité | agent_scolarite | password | `/agent` |
| Admin | admin | password | `/admin` |

---

## Proxy Vite (vite.config.js)

Le proxy redirige automatiquement vers les microservices :

| Préfixe | Service | Port |
|---------|---------|------|
| `/api/auth` | auth_service | 8001 |
| `/api/inscriptions` | inscription_service | 8002 |
| `/api/dossiers`, `/api/formations` | dossier_service | 8003 |
| `/api/deliberations`, `/api/resultats` | deliberation_service | 8004 |
| `/api/attestations` | attestation_service | 8005 |
| `/api/notifications`, `/api/chatbot` | notification_service | 8006 |
| `/api/evaluer`, `/api/regles` | ia_service | 8007 |
| `/api/audit` | audit_service | 8008 |
