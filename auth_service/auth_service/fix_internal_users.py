import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_service.settings")
django.setup()

from accounts.models import Utilisateur, Role

needed = [
    ("service_attestation", "service_attestation_secret_2025"),
    ("service_ia", "service_ia_secret_2025"),
    ("service_notification", "service_notification_secret_2025"),
    ("service_inscription", "service_inscription_secret_2025"),
    ("service_deliberation", "service_deliberation_secret_2025"),
    ("service_dossier", "service_dossier_secret_2025"),
]

admin_role, _ = Role.objects.get_or_create(libelle="admin")

results = []
for username, password in needed:
    user, created = Utilisateur.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@uadb.local",
            "is_active": True,
            "etat_compte": "actif",
        },
    )

    user.is_active = True
    user.etat_compte = "actif"
    user.set_password(password)
    user.save()
    user.roles.add(admin_role)

    results.append({"username": username, "created": created})

print("DONE")
for item in results:
    print(item)
