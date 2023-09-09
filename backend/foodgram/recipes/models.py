from django.core import validators
from django.db import models
from colorfield.fields import ColorField

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True,
                            verbose_name='Название')
    color = ColorField('Цвет в HEX', default='#aaa3ff')
    slug = models.SlugField(max_length=200, unique=True,
                            verbose_name='Уникальный слаг')

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=False,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=200,
                                        verbose_name='Единица измерения')

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes', verbose_name='Автор')
    image = models.ImageField(upload_to='recipes/', verbose_name='Изображение')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=(
            validators.MinValueValidator(
                1,
                'Минимальное время приготовления не может быть меньше минуты'
            ),
        )
    )
    tags = models.ManyToManyField(Tag, through='RecipeTag',
                                  verbose_name='Теги')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         verbose_name='Ингредиенты')

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_tags',
                               verbose_name='Рецепт')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='tag_recipes', verbose_name='Тег')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Тег в рецепте'
        verbose_name_plural = 'Теги в рецептах'
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'tag'],
            name='unique_tags_recipe'
        )]

    def __str__(self):
        return str(self.tag)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredients',
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredient_recipes',
                                   verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=(
            validators.MinValueValidator(
                1,
                'Минимальное количество ингредиента не может быть меньше 1'
            ),
        )
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_ingredients_recipe'
        )]

    def __str__(self):
        return str(self.ingredient)


class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='cart', verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='cart', verbose_name='Рецепт')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_cart_user')
        ]

    def __str__(self):
        return f'{self.recipe} в корзине {self.user}'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites',
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorites',
                               verbose_name='Рецепт')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_favorite'
        )]
