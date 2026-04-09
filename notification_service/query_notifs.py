#!/usr/bin/env python
"""
Query notifications from database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notification_service.settings')
django.setup()

from notification.models import Notification

print('\n=== NOTIFICATIONS POUR ÉTUDIANT 10 ===')
notifs = Notification.objects.filter(etudiant_id=10).order_by('-date_notification')
print(f'TOTAL: {notifs.count()}\n')

for n in notifs:
    print(f'ID: {n.id} | Type: {n.type_notification:20} | Statut: {n.statut_envoi:10} | Date: {str(n.date_notification)[:19]}')
    print(f'    Message: {n.message[:70]}')
    if n.erreur:
        print(f'    ❌ ERREUR: {n.erreur}')
    print()
