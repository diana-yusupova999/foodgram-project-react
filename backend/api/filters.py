from django_filters import rest_framework as django_filters

from django.contrib.auth import get_user_model

from ..recipes.models import Ingredient, Recipe, Tag


User = get_user_model()


class SubscriptionsFilter(django_filters.FilterSet):
    """Фильтрация избранного и списка покупок."""

    recipes_limit = django_filters.NumberFilter(method="get_queryset")

    class Meta:
        """Метакласс фильтра."""

        model = Recipe
        fields = ["recipes_limit"]

    def get_queryset(self, queryset, name, value):
        """Определяет, какие объекты следует фильтровать."""
        if name == "recipes_limit":
            return queryset[:3]
        return queryset


class FavoriteAndShoppingCartFilter(django_filters.FilterSet):
    """Фильтрация избранного и списка покупок."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    is_in_shopping_cart = django_filters.NumberFilter(method="get_queryset")
    is_favorited = django_filters.NumberFilter(method="get_queryset")

    class Meta:
        """Метакласс фильтра."""

        model = Recipe
        fields = ["tags", "author", "is_favorited", "is_in_shopping_cart"]

    def get_queryset(self, queryset, name, value):
        """Определяет, какие объекты следует фильтровать."""
        if name == "is_in_shopping_cart":
            return queryset.filter(in_carts__user=self.request.user)
        if name == "is_favorited":
            return queryset.filter(in_favorites__user=self.request.user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    """Фильтрация ингредиентов."""

    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        """Метакласс фильтра."""

        model = Ingredient
        fields = ("name",)
