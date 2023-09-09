"""Модуль, содержащий модели Django-приложения users."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        null=False,
        verbose_name="Email",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                r"^[\w.@+-]+$",
                "Используйте только буквы, цифры и символы @/./+/-/_",
                "invalid_username",
            )
        ],
        verbose_name="Username",
    )
    first_name = models.CharField(max_length=150, verbose_name="Имя")
    last_name = models.CharField(max_length=150, verbose_name="Фамилия")
    is_subscribed = models.BooleanField(default=False, verbose_name="Подписан")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        """Метакласс модели пользователя."""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return self.username


class Subscription(models.Model):
    """Модель подписки."""

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="Автор",
    )

    class Meta:
        """Метакласс модели подписки."""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"{self.follower.username} follows {self.author.username}"
