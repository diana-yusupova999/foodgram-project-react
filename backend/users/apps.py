"""Модуль, содержащий класс настроек приложения users."""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Класс настроек приложения users."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
