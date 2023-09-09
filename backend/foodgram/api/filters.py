import django_filters
from django.db.models.functions import Lower

from recipes.models import User, Recipe, Tag, Ingredient


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = django_filters.NumberFilter(method="is_favorited_filter")
    is_in_shopping_cart = django_filters.NumberFilter(
        method="is_in_shopping_cart_filter")

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def is_favorited_filter(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)

    def sort_ingredients(self, queryset, name, value):
        ingredient_query = self.request.query_params.get("name")

        if ingredient_query:
            for i, _ in enumerate(ingredient_query, start=1):
                queryset = queryset.filter(
                    name__istartswith=ingredient_query[:i]
                )

        queryset = queryset.annotate(lower_name=Lower("name"))
        queryset = queryset.order_by("lower_name")
        return queryset
