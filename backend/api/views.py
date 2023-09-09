from io import StringIO

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ..recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)
from ..users.models import Subscription, User
from .filters import FavoriteAndShoppingCartFilter, IngredientFilter
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    ChangePasswordSerializer, IngredientSerializer, RecipeCreateSerializer,
    RecipeFullSerializer, RecipeSerializer, SubscriptionSerializer,
    TagSerializer, UserSerializer,
)


class UserView(viewsets.ModelViewSet):
    """Представление для пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_serializer(self, *args, **kwargs):
        """Метод для получения сериалайзера."""
        kwargs["context"] = {"request": self.request}
        return super().get_serializer(
            *args,
            **kwargs,
        )

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Метод для информации о текущем пользователе."""
        return Response(
            UserSerializer(
                request.user,
                context={
                    "request": request,
                },
            ).data
        )

    @action(
        detail=False, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Метод для изменения пароля пользователя."""
        serializer = ChangePasswordSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.check_password(
            serializer.validated_data["current_password"]
        ):
            request.user.set_password(
                serializer.validated_data["new_password"]
            )
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError("Текущий пароль неверный.")

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Метод для получения списка подписок пользователя."""
        self.queryset = Subscription.objects.filter(
            follower=request.user
        ).annotate(recipes_count=Count("author__recipes"))
        queryset = self.paginate_queryset(self.queryset)
        recipes_limit = int(request.query_params.get("recipes_limit", 6))
        serializer = SubscriptionSerializer(
            queryset,
            many=True,
            context={"request": request, "recipes_limit": recipes_limit},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        """Метод для подписки пользователей."""
        target_user = get_object_or_404(User, id=pk)

        if target_user == request.user:
            return Response(
                {"error": "Вы не можете взаимодействовать с собой."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = Subscription.objects.get_or_create(
            follower=request.user, author=target_user
        )
        if not created:
            return Response(
                {"error": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"success": "Вы успешно подписались на пользователя."},
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Метод для отписки пользователей."""
        amount, _ = Subscription.objects.filter(
            follower=request.user, author_id=pk
        ).delete()
        if not amount:
            return Response(
                {"errors": "Рецепт не найден в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagView(viewsets.ModelViewSet):
    """Представление для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientView(viewsets.ModelViewSet):
    """Представление для ингредиентов."""

    permission_classes = [AllowAny]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeView(viewsets.ModelViewSet):
    """Представление для рецептов."""

    pagination_class = PageNumberPagination
    queryset = Recipe.objects.prefetch_related(
        "tags", "ingredients"
    ).select_related("author")
    serializer_class = RecipeFullSerializer
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FavoriteAndShoppingCartFilter

    def get_serializer(self, *args, **kwargs):
        """Получение сериализатора с контекстом запроса."""
        return super().get_serializer(
            *args, **kwargs, context={"request": self.request}
        )

    def get_permissions(self):
        """Проверка аутентификации пользователя."""
        if self.action == "create":
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Метод создания рецепта."""
        serializer = RecipeCreateSerializer(
            data=request.data, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        response_serializer = RecipeFullSerializer(
            recipe, context={"request": request}
        )
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )

    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Метод для добавления рецепта в избранное."""
        recipe = self.get_object()
        user = request.user

        if FavoriteRecipe.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"errors": "Рецепт уже добавлен в избранное."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        FavoriteRecipe.objects.create(user=user, recipe=recipe)
        serializer = RecipeSerializer(recipe)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        """Метод для удаления рецепта в избранное."""
        user = request.user
        recipe = self.get_object()

        amount, _ = FavoriteRecipe.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if not amount:
            return Response(
                {"errors": "Рецепт не найден в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        """Метод для изменения рецепта."""
        instance = self.get_object()

        serializer = RecipeCreateSerializer(
            instance,
            data=request.data,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            response_serializer = RecipeFullSerializer(
                instance, context={"request": request}
            )
            return Response(
                response_serializer.data, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления рецепта в список покупок."""
        recipe = self.get_object()
        user = request.user

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"errors": "Рецепт уже добавлен в список покупок."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeSerializer(recipe)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        """Метод для удаления рецепта из списка покупок."""
        recipe = self.get_object()
        user = request.user
        amount, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if not amount:
            return Response(
                {"errors": "Рецепт не найден в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"message": "Рецепт успешно удален из списка покупок."},
            status=status.HTTP_204_NO_CONTENT,
        )

    def generate_shopping_list(self):
        """Метод для создания текстового файла списка покупок."""
        user = self.request.user
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in_carts__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_quantity=Sum("amount"))
        )
        txt_buffer = StringIO()
        txt_buffer.write("Список покупок:\n\n")
        for ingredient in ingredients:
            txt_buffer.write(
                f"- {ingredient['ingredient__name']}: "
                f"{ingredient['total_quantity']} "
                f"{ingredient['ingredient__measurement_unit']}\n"
            )
        txt_buffer.seek(0)
        return txt_buffer

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        """Метод для скачивания списка покупок."""
        txt_buffer = self.generate_shopping_list()
        response = HttpResponse(txt_buffer, content_type="text/plain")
        response[
            "Content-Disposition"
        ] = "attachment; filename='shopping_list.txt'"
        return response
