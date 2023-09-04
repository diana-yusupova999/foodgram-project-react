from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F


class User(AbstractUser):
    """Модель пользователя."""
    ADMIN = 'admin'
    USER = 'user'

    ROLES = [
        (ADMIN, 'admin'),
        (USER, 'user'),
    ]
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True
    )
    username = models.CharField(verbose_name='Уникальный юзернейм', max_length=150, unique=True)
    first_name = models.CharField(verbose_name='Имя', max_length=150, blank=True)
    last_name = models.CharField(verbose_name='Фамилия', max_length=150, blank=True)
    password = models.CharField(verbose_name='Пароль', max_length=150)
    # bio = models.TextField('биография', blank=True)
    role = models.CharField('роль', max_length=10, choices=ROLES, default=USER)
    # confirmation_code = models.CharField(
    #     'код подтверждения', max_length=100, null=True, blank=True
    # )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        """Проверка на права администратора."""
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_user(self):
        """Проверка на права пользователя."""
        return self.role == self.USER


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name="Автор",
    )

    class Meta:
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique_follow'
            ),
            models.CheckConstraint(
                check=~Q(following=F('user')), name='fields_must not be equal'
            ),
        ]
