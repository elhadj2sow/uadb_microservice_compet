import json
import requests

LOGIN_URL = "http://localhost:8001/api/auth/login/"
TRACER_URL = "http://localhost:8008/api/audit/tracer/"
JOURNAL_URL = "http://localhost:8008/api/audit/journal/?service=inscription&ressource_id=21&limit=20"

login_resp = requests.post(
    LOGIN_URL,
    json={"username": "agent_scolarite", "password": "pass1234"},
    timeout=20,
)
login_resp.raise_for_status()
access = login_resp.json()["access"]
headers = {"Authorization": f"Bearer {access}"}

payment_like_event = {
    "action": "UPDATE",
    "service": "inscription",
    "utilisateur_id": 20,
    "acteur": "agent_scolarite",
    "role_acteur": "agent_scolarite",
    "description": "Payment confirme via PayTech - inscription ID:21",
    "ressource": "inscription/21/paiement",
    "ressource_id": 21,
    "ressource_type": "Inscription",
    "etudiant_id": 20,
    "inscription_id": 21,
    "niveau": "INFO",
    "statut": "succes",
    "details": {
        "event_type": "PAYMENT",
        "provider": "paytech",
        "statut": "confirme",
        "montant": "25000.00",
    },
}

workflow_step_event = {
    "action": "WORKFLOW_STEP",
    "service": "inscription",
    "utilisateur_id": 20,
    "acteur": "agent_scolarite",
    "role_acteur": "agent_scolarite",
    "description": "Passage workflow vers etape medicale - inscription ID:21",
    "ressource": "inscription/21/workflow",
    "ressource_id": 21,
    "ressource_type": "Inscription",
    "etudiant_id": 20,
    "inscription_id": 21,
    "niveau": "INFO",
    "statut": "succes",
    "details": {"etape": "medical", "ordre": 3},
}

pay_resp = requests.post(TRACER_URL, json=payment_like_event, headers=headers, timeout=20)
pay_resp.raise_for_status()
step_resp = requests.post(TRACER_URL, json=workflow_step_event, headers=headers, timeout=20)
step_resp.raise_for_status()

journal_resp = requests.get(JOURNAL_URL, headers=headers, timeout=20)
journal_resp.raise_for_status()
journal = journal_resp.json()

print("PAYMENT_LIKE_EVENT_ID=", pay_resp.json().get("id"))
print("WORKFLOW_STEP_ID=", step_resp.json().get("id"))
print("COUNT=", journal.get("count"))

rows = []
for item in journal.get("results", [])[:12]:
    rows.append(
        {
            "id": item.get("id"),
            "action": item.get("action"),
            "description": item.get("description"),
            "date_action": item.get("date_action"),
        }
    )

print(json.dumps(rows, ensure_ascii=True, indent=2))
