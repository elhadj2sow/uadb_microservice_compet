from django.apps import AppConfig


class DeliberationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'deliberation'
    verbose_name       = 'Gestion des Délibérations'

    def ready(self):
        import deliberation.signals  # noqa: F401
