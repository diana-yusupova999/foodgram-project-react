from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe
from users.models import User


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


class TagFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(method='favorite_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter'
    )

    def favorite_filter(self, queryset, name, value):
        if not self.request.user.is_anonymous and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        if not self.request.user.is_anonymous and value:
            return queryset.filter(cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags')
