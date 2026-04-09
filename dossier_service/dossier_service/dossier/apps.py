from django.apps import AppConfig


class DossierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'dossier'
    verbose_name       = 'Gestion des Dossiers Étudiants'

    def ready(self):
        import dossier.signals  # noqa: F401
