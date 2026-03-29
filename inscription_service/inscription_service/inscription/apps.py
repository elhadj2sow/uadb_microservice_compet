from django.apps import AppConfig


class InscriptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'inscription'
    verbose_name       = 'Inscription Administrative'

    def ready(self):
        import inscription.signals  # noqa: F401 — connecte les signaux
