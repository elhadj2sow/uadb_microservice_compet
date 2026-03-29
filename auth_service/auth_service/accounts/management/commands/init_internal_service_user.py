from decouple import config
from django.core.management.base import BaseCommand

from accounts.models import Role, Utilisateur


class Command(BaseCommand):
    help = (
        "Crée ou met à jour l'utilisateur interne pour les appels "
        "inter-services (service inscription -> auth)."
    )

    def handle(self, *args, **kwargs):
        username = config("SERVICE_INTERNAL_USER", default="service_inscription")
        password = config(
            "SERVICE_INTERNAL_PASSWORD",
            default="service_inscription_secret_2025",
        )

        user, created = Utilisateur.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@internal.local",
                "is_active": True,
                "etat_compte": "actif",
            },
        )

        user.is_active = True
        user.etat_compte = "actif"
        user.set_password(password)
        user.save()

        role_admin, _ = Role.objects.get_or_create(libelle="admin")
        user.roles.add(role_admin)

        state = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(
            f"✔ Utilisateur interne {state} : {username}"
        ))
        self.stdout.write(self.style.SUCCESS(
            "✔ Rôle admin attribué (ou déjà présent)."
        ))
