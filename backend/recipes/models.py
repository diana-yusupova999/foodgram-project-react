from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.contrib.auth import get_user_model
from colorfield.fields import ColorField


User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(verbose_name='Название ингредиента', max_length=200, )
    measurement_unit = models.CharField(verbose_name='Единица измерения', max_length=50, )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(verbose_name="Название", max_length=200, unique=True, )
    color = ColorField(verbose_name="Цвет", default="#FF0000",)
    slug = models.SlugField(
        verbose_name="Slug",
        max_length=200,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[-a-zA-Z0-9_]+$",
                message="Slug не может содержать такие символы.",
                code="invalid_slug",
            )
        ],
    )

    def __str__(self):
        """Возвращает строковое представление объекта тега."""
        return self.name


class Recipe(models.Model):
    name = models.CharField(verbose_name='Название', max_length=200, )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, )
    ingredients = models.ManyToManyField(verbose_name='Список ингредиентов', to=Ingredient, )
    tags = models.ManyToManyField(verbose_name='Список id тегов', related_name='recipes', to=Tag, )
    image = models.ImageField(verbose_name='Изображение', upload_to='recipes/', )
    text = models.CharField(verbose_name='Описание', )
    cooking_time = models.PositiveIntegerField(verbose_name='Время приготовления (в минутах)', )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации", )

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self):
        return {self.name}


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(to=Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')
    ingredient = models.ForeignKey(to=Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество в рецепте',
        validators=[MinValueValidator(1, message='Минимальное количество = 1')],
    )

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}, {self.amount}'


class ShoppingCart(models.Model):
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
        unique_together = ["user", "recipe"]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class FavoriteRecipe(models.Model):
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
        verbose_name = "Избранные рецепты"
        verbose_name_plural = "Избранные рецепты"
        unique_together = ["user", "recipe"]

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"
