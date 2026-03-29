from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Crée le schéma PostgreSQL inscription et initialise les données'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== Initialisation du schéma inscription ===\n')

        with connection.cursor() as cursor:

            # 1. Créer le schéma
            cursor.execute("CREATE SCHEMA IF NOT EXISTS inscription;")
            self.stdout.write(self.style.SUCCESS('✔ Schéma inscription créé'))

            # 2. Vérifier que les tables existent
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'inscription'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            self.stdout.write(
                f'  Tables existantes : {tables or "aucune"}'
            )

        self.stdout.write(self.style.SUCCESS(
            '\n=== Schéma prêt. Lancez maintenant : '
            'python manage.py migrate ==='
        ))
