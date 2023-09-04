from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Ingredient(models.Model):
    id = models.IntegerField(verbose_name='Уникальный id', unique=True)
    amount = models.IntegerField(verbose_name='Количество в рецепте')


class Recipes(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL)
    ingredients = models.ManyToManyField(verbose_name='Список ингредиентов', to='Ingredient',)
    tags = models.ManyToManyField(verbose_name='Список id тегов', related_name="recipes", to='Tag',)
    image = models.ImageField(verbose_name='Картинка, закодированная в Base64')
    name = models.CharField(verbose_name='Название', max_length=200)
    text = models.CharField(verbose_name='Описание')
    cooking_time = models.IntegerField(verbose_name='Время приготовления (в минутах)')


class ShoppingList(models.Model):
    pass


class FavoriteRecipe(models.Model):
    pass


class IngredientAmount(models.Model):
    pass


class Tag(models.Model):
    pass
