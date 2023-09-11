from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingList,
    Tag,
    User,
    Subscription
)


class TagInline(admin.TabularInline):
    model = Recipe.tags.through


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "count_favorites",)
    search_fields = ("author__username", "author__email",
                     "author__first_name", "author__last_name",)
    list_filter = ("author", "name", "tags",)
    ordering = ("name",)
    empty_value_display = "-пусто-"
    inlines = [TagInline, IngredientInline]

    def count_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    count_favorites.short_description = 'Количество избранных'


class UserAdmin(UserAdmin):
    model = User
    list_display = ("username", "email", "first_name", "last_name")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("email", "username")
    ordering = ("id",)
    empty_value_display = "-пусто-"


admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredients)
admin.site.register(Favorite)
admin.site.register(ShoppingList)
admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
