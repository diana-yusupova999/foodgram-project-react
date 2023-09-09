from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag,
                     ShoppingCart, Tag)


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    min_num = 1
    extra = 1


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    empty_value_display = "---"
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name',)
    empty_value_display = "---"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline, RecipeTagInline)
    list_display = ('id', 'name', 'author', 'image', 'text', 'cooking_time',
                    'favorites')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = "---"

    def favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    empty_value_display = "---"


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'tag')
    list_filter = ('recipe', 'tag')
    empty_value_display = "---"


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    empty_value_display = "---"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    empty_value_display = "---"
