from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'Онигири — доставка еды'

    def ready(self):
        """Подключает сигналы приложения."""
        import api.signals  # noqa: F401
