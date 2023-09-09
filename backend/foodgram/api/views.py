from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from users.serializers import FollowRecipeSerializer
from .filters import IngredientSearchFilter, TagFilter
from .pagination import CustomPageNumberPagination
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from .serializers import IngredientSerializer, RecipeSerializer, TagSerializer


class TagsViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = TagFilter

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def add_obj(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже добавлен в список'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        return Response(
            FollowRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete_obj(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт не в списке'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(Favorite, request.user, pk)
        if request.method == 'DELETE':
            return self.delete_obj(Favorite, request.user, pk)
        return None

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(ShoppingCart, request.user, pk)
        if request.method == 'DELETE':
            return self.delete_obj(ShoppingCart, request.user, pk)
        return None

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__cart__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            name=F('ingredient__name'),
            units=F('ingredient__measurement_unit'),
            total=Sum('amount'),
        )
        shopping_list = 'Список покупок:\n\n'
        for number, ingredient in enumerate(ingredients, start=1):
            shopping_list += (
                f'{ingredient["name"]}: '
                f'{ingredient["total"]} '
                f'{ingredient["units"]}\n')

        cart = 'shopping-list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (f'attachment;'
                                           f'filename={cart}')
        return response
