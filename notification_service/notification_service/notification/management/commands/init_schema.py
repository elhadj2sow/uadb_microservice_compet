from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Crée le schéma PostgreSQL notification'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== Initialisation schéma notification ===\n')
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE SCHEMA IF NOT EXISTS notification;"
            )
            self.stdout.write(
                self.style.SUCCESS('✔ Schéma notification créé')
            )
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'notification'
                ORDER BY table_name;
            """)
            tables = [r[0] for r in cursor.fetchall()]
            self.stdout.write(
                f'  Tables existantes : '
                f'{tables or "aucune (normal avant migrate)"}'
            )
        self.stdout.write(self.style.SUCCESS(
            '\nLancez maintenant : python manage.py migrate'
        ))
