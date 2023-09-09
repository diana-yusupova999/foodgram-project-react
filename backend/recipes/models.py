"""Модуль, содержащий модели Django-приложения recipes."""
from colorfield.fields import ColorField

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


User = get_user_model()


class Tag(models.Model):
    """Модель для хранения информации о тегах."""

    name = models.CharField(
        max_length=200, unique=True, verbose_name="Название"
    )
    color = ColorField(
        default="#FF0000",
        verbose_name="Цвет",
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[-a-zA-Z0-9_]+$",
                message="Slug не может содержать такие символы.",
                code="invalid_slug",
            )
        ],
        verbose_name="Slug",
    )

    class Meta:
        """Метакласс модели тэг."""

        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

    def __str__(self):
        """Возвращает строковое представление объекта тега."""
        return self.name


class Ingredient(models.Model):
    """Модель для хранения информации об ингредиентах рецептов."""

    name = models.CharField(max_length=200, verbose_name="Название")
    measurement_unit = models.CharField(
        max_length=200, verbose_name="Единица измерения"
    )

    class Meta:
        """Метакласс модели ингредиент."""

        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        """Возвращает строковое представление объекта ингредиента."""
        return self.name


class Recipe(models.Model):
    """Модель для хранения информации о рецептах."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(upload_to="recipes/", verbose_name="Изображение")
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="in_recipes",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag, related_name="recipes", verbose_name="Теги"
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Время приготовления (в минутах)",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )

    class Meta:
        """Метакласс модели рецепт."""

        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return self.name


class RecipeIngredient(models.Model):
    """Модель для хранения информации о ингредиентах в рецептах."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="amount",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="amout",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], verbose_name="Количество"
    )

    class Meta:
        """Метакласс модели о ингредиентах в рецепте."""

        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиента"

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"{self.ingredient} – {self.amount}"


class FavoriteRecipe(models.Model):
    """Модель для хранения информации о рецептах, добавленных в избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_favorites",
        verbose_name="Рецепт",
    )

    class Meta:
        """Метакласс модели информации о рецептах."""

        verbose_name = "Избранные рецепты"
        verbose_name_plural = "Избранные рецепты"
        unique_together = ["user", "recipe"]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingCart(models.Model):
    """Модель для рецептов, добавленных в список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_carts",
        verbose_name="Рецепт",
    )

    class Meta:
        """Метакласс модели списка покупок."""

        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        unique_together = ["user", "recipe"]

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f"{self.user.username} - {self.recipe.name}"
