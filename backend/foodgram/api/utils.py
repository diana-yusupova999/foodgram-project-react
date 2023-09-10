from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from ..recipes.models import Recipe


def add_favorite_shoppinglist(request, pk, model, serializer):
    recipe = get_object_or_404(Recipe, pk=pk)
    if model.objects.filter(user=request.user, recipe=recipe).exists():
        return Response(
            {"errors": "Рецепт уже есть в избранном или в списке покупок"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    model.objects.get_or_create(user=request.user, recipe=recipe)
    data = serializer(recipe).data
    return Response(data, status=status.HTTP_201_CREATED)


def remove_favorite_shoppinglist(request, pk, model):
    recipe = get_object_or_404(Recipe, pk=pk)
    if model.objects.filter(user=request.user, recipe=recipe).exists():
        follow = get_object_or_404(model, user=request.user,
                                   recipe=recipe)
        follow.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
    return Response(
        {"errors": "Рецепта нет в избраном или в списке покупок"},
        status=status.HTTP_400_BAD_REQUEST
    )


def recipe_ingredient_create(ingredients_data, models, recipe):
    bulk_create_data = (
        models(
            recipe=recipe,
            ingredient=ingredient_data["ingredient"],
            amount=ingredient_data["amount"])
        for ingredient_data in ingredients_data
    )
    models.objects.bulk_create(bulk_create_data)
