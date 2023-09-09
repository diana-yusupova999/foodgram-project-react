from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Класс настроек приложения API."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
