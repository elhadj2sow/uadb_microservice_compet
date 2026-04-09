#!/usr/bin/env python
import os
import sys
import django

# Set path to auth_service directory
sys.path.insert(0, r'c:\Users\Dell\OneDrive\Bureau\microservices_uadb\auth_service\auth_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
os.chdir(r'c:\Users\Dell\OneDrive\Bureau\microservices_uadb\auth_service\auth_service')

django.setup()

from accounts.models import Utilisateur, Role, Etudiant

# Créer enseignant
try:
    u1, created = Utilisateur.objects.get_or_create(
        username='enseignant',
        defaults={'email': 'enseignant@uadb.edu', 'is_active': True}
    )
    u1.set_password('pass1234')
    u1.save()
    role = Role.objects.get(libelle='enseignant')
    u1.roles.add(role)
    print('✅ enseignant / pass1234')
except Exception as e:
    print(f'❌ enseignant: {e}')

# Créer responsable_pedagogique
try:
    u2, created = Utilisateur.objects.get_or_create(
        username='responsable_pedagogique',
        defaults={'email': 'responsable@uadb.edu', 'is_active': True}
    )
    u2.set_password('pass1234')
    u2.save()
    role = Role.objects.get(libelle='responsable_pedagogique')
    u2.roles.add(role)
    print('✅ responsable_pedagogique / pass1234')
except Exception as e:
    print(f'❌ responsable_pedagogique: {e}')

# Créer étudiant (si n'existe pas)
try:
    u3, created = Utilisateur.objects.get_or_create(
        username='etudiant1',
        defaults={'email': 'etudiant@uadb.edu', 'is_active': True}
    )
    u3.set_password('pass1234')
    u3.save()
    role = Role.objects.get(libelle='etudiant')
    u3.roles.add(role)
    
    # Créer profil Etudiant
    etud, _ = Etudiant.objects.get_or_create(
        utilisateur=u3,
        defaults={'ine': 'INE000001', 'matricule': 'MAT000001', 'etat': 'actif'}
    )
    print(f'✅ etudiant1 / pass1234 | matricule: MAT000001')
except Exception as e:
    print(f'❌ etudiant1: {e}')

# Créer jury (admin)
try:
    u4, created = Utilisateur.objects.get_or_create(
        username='jury',
        defaults={'email': 'jury@uadb.edu', 'is_active': True}
    )
    u4.set_password('pass1234')
    u4.save()
    role = Role.objects.get(libelle='admin')
    u4.roles.add(role)
    print('✅ jury / pass1234')
except Exception as e:
    print(f'❌ jury: {e}')

print('\n✅ Tous les comptes sont prêts pour les tests!')
print('   - enseignant / pass1234')
print('   - responsable_pedagogique / pass1234')
print('   - etudiant1 / pass1234')
print('   - jury / pass1234')
