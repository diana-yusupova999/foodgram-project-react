from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from colorfield.fields import ColorField

from .validators import validate_username


class User(AbstractUser):
    """Модель пользователей."""
    USER = "user"
    ADMIN = "admin"

    USER_ROLES = [
        (USER, "Пользователь"),
        (ADMIN, "Администратор")
    ]
    username = models.CharField(
        validators=(validate_username,),
        max_length=150,
        verbose_name="Имя пользователя",
        unique=True,
    )
    email = models.EmailField(
        max_length=254,
        verbose_name="Электронная почта",
        unique=True,
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия",
    )
    password = models.CharField(
        max_length=150,
        verbose_name="Пароль",
    )
    role = models.CharField(
        max_length=20,
        verbose_name="Роль",
        default=USER,
        choices=USER_ROLES
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "password"]

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == User.ADMIN or self.is_superuser

    @property
    def is_user(self):
        return self.role == User.USER


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название тега")
    color = ColorField(default='#FF0000')
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="Идентификатор тега")

    class Meta:
        ordering = ("name",)
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        max_length=200,
        verbose_name="Название ингредиента")
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name="Единица измерения ингредиента")

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        models.UniqueConstraint(
            fields=["name", "measurement_unit"],
            name="unique_measurement_unit_for_name"
        )

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipe",
        verbose_name="Автор рецепта")
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название рецепта")
    image = models.ImageField(
        upload_to="recipes/",
        blank=True,
        null=True,
        verbose_name="Изображение")
    text = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание рецепта")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredients",
        related_name="ingredients",
        verbose_name="Игредиент для рецепта")
    tags = models.ManyToManyField(
        Tag,
        related_name="tags",
        verbose_name="Тег к рецепту")
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, "Минимум"),
            MaxValueValidator(600, "Максимум")
        ],
        blank=True,
        null=True,
        verbose_name="Время приготовления (в минутах)")
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации рецепта")

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """Модель количества ингредиентов,
    необходимых для рецепта."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт")
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Игредиент")
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1, "Минимум")],
        verbose_name="Количество ингредиентов")

    class Meta:
        verbose_name = "Ингредиент_в_рецепте"
        verbose_name_plural = "Ингредиенты_в_рецепте"

    def __str__(self):
        return (f"{self.ingredient.name} ({self.ingredient.measurement_unit})"
                f" - {self.amount}")


class Subscription(models.Model):
    """Модель подписки."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(check=~models.Q(author=models.F('user')),
                                   name='author_not_user'),
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Favorite(models.Model):
    """Модель списка избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_recipe",
        verbose_name="Пользователь")
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite_recipe",
        verbose_name="Рецепт")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_favorite_recipe"),)

    def __str__(self):
        return f"Рецепт {self.recipe} добавлен в избранное к {self.user}"


class ShoppingList(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_list",
        null=True,
        verbose_name="Пользователь")
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_list",
        verbose_name="Рецепт")

    class Meta:
        verbose_name = "Cписок покупок"
        verbose_name_plural = "Списки покупок"
        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_shopping_list"),)

    def __str__(self):
        return f"Рецепт {self.recipe} добавлен в список покупок к {self.user}"
