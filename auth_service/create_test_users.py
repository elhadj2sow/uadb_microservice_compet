#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_service.settings")
BASE_DIR = Path(__file__).resolve().parent / "auth_service"
sys.path.insert(0, str(BASE_DIR))
django.setup()

from accounts.models import Utilisateur, Etudiant, Role

# Créer les rôles
admin_role, _ = Role.objects.get_or_create(libelle="admin")
etudiant_role, _ = Role.objects.get_or_create(libelle="etudiant")
enseignant_role, _ = Role.objects.get_or_create(libelle="enseignant")
responsable_role, _ = Role.objects.get_or_create(libelle="responsable_pedagogique")
scolarite_role, _ = Role.objects.get_or_create(libelle="agent_scolarite")

print("✅ Roles created")

# Créer responsable_pedagogique
resp_user, created = Utilisateur.objects.get_or_create(
    username="responsable_pedagogique",
    defaults={
        "email": "responsable@uadb.edu",
        "is_active": True,
        "etat_compte": "actif",
    }
)
resp_user.is_active = True
resp_user.etat_compte = "actif"
resp_user.set_password("pass1234")
resp_user.save()
resp_user.roles.add(responsable_role)
print(f"✅ responsable_pedagogique | password: pass1234")

# Créer enseignant
ens_user, created = Utilisateur.objects.get_or_create(
    username="enseignant",
    defaults={
        "email": "enseignant@uadb.edu",
        "is_active": True,
        "etat_compte": "actif",
    }
)
ens_user.is_active = True
ens_user.etat_compte = "actif"
ens_user.set_password("pass1234")
ens_user.save()
ens_user.roles.add(enseignant_role)
print(f"✅ enseignant | password: pass1234")

# Créer étudiant
etud_user, created = Utilisateur.objects.get_or_create(
    username="etudiant",
    defaults={
        "email": "etudiant@uadb.edu",
        "is_active": True,
        "etat_compte": "actif",
    }
)
etud_user.is_active = True
etud_user.etat_compte = "actif"
etud_user.set_password("pass1234")
etud_user.save()
etud_user.roles.add(etudiant_role)

# Créer profil Etudiant
etudiant_profile, _ = Etudiant.objects.get_or_create(
    utilisateur=etud_user,
    defaults={
        "ine": "INE123456789",
        "matricule": "M123456789",
        "nom": "Test",
        "prenom": "Etudiant",
        "statut": "actif"
    }
)
print(f"✅ etudiant | password: pass1234 | matricule: M123456789")

# Créer agent_scolarite
sco_user, created = Utilisateur.objects.get_or_create(
    username="agent_scolarite",
    defaults={
        "email": "scolarite@uadb.edu",
        "is_active": True,
        "etat_compte": "actif",
    }
)
sco_user.is_active = True
sco_user.etat_compte = "actif"
sco_user.set_password("pass1234")
sco_user.save()
sco_user.roles.add(scolarite_role)
print(f"✅ agent_scolarite | password: pass1234")

# Créer jury (admin)
jury_user, created = Utilisateur.objects.get_or_create(
    username="jury",
    defaults={
        "email": "jury@uadb.edu",
        "is_active": True,
        "etat_compte": "actif",
    }
)
jury_user.is_active = True
jury_user.etat_compte = "actif"
jury_user.set_password("pass1234")
jury_user.save()
jury_user.roles.add(admin_role)
print(f"✅ jury (admin) | password: pass1234")

print("\n" + "="*50)
print("📋 All test accounts created successfully!")
print("="*50)
