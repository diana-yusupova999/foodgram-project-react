import io

from django.db.models import Sum
from django.conf import settings
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.filters import SearchFilter
from rest_framework import status
from rest_framework.decorators import action

from api.serializers import (TagSerializer, UserSerializer, RecipeSerializer,
                             IngredientSerializer, FollowSerializer,
                             RecipeGetSerializer, RecipeFollowSerializer,)
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (Tag, User, Recipe, Ingredient, Favorite,
                            ShoppingList, Subscription, RecipeIngredients)
from api.utils import (add_favorite_shoppinglist, remove_favorite_shoppinglist)
from api.filters import RecipeFilter, IngredientFilter
from api.paginations import CastomPagination


class ShoppingListDownloadView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        shopping_list = RecipeIngredients.objects.filter(
            recipe__shopping_list__user=request.user).values(
            "ingredient__name",
            "ingredient__measurement_unit"
        ).annotate(
            amount=Sum("amount")
        ).order_by()
        font = "Tantular"
        pdfmetrics.registerFont(
            TTFont("Tantular",
                   "./data/Tantular.ttf",
                   "UTF-8")
        )
        buffer = io.BytesIO()
        pdf_file = canvas.Canvas(buffer)
        pdf_file.setFont(font, settings.SETFONTS)
        pdf_file.drawString(
            settings.TITLE_X,
            settings.TITLE_Y,
            "Список покупок:"
        )
        pdf_file.setFont(font, settings.SETFONT)
        from_bottom = settings.BOTTOM_Y
        for number, ingredient in enumerate(shopping_list, start=1):
            pdf_file.drawString(
                settings.ITEM_X,
                from_bottom,
                (f'{number}.  {ingredient["ingredient__name"]} - '
                 f'{ingredient["amount"]} '
                 f'{ingredient["ingredient__measurement_unit"]}')
            )
            from_bottom -= settings.ITEM_HEIGHT
            if from_bottom <= settings.MAX_Y:
                from_bottom = settings.TITLE_Y
                pdf_file.showPage()
                pdf_file.setFont(font, settings.SETFONT)
        pdf_file.showPage()
        pdf_file.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename="shopping_list.pdf"
        )


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViwsSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = IngredientFilter
    ordering_fields = ("name",)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CastomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeGetSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action != "create":
            return (IsAuthorOrReadOnly(),)
        return super().get_permissions()

    @action(detail=True, methods=["POST", "DELETE"],)
    def favorite(self, request, pk):
        if self.request.method == "POST":
            return add_favorite_shoppinglist(request, pk, Favorite,
                                             RecipeFollowSerializer)
        return remove_favorite_shoppinglist(request, pk, Favorite)

    @action(detail=True, methods=["POST", "DELETE"],)
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return add_favorite_shoppinglist(request, pk, ShoppingList,
                                             RecipeFollowSerializer)
        return remove_favorite_shoppinglist(request, pk, ShoppingList)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CastomPagination

    @action(
        detail=True, permission_classes=[IsAuthenticated],
        methods=["post", "delete"]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=self.kwargs.get("id"))

        if request.method == "POST":
            if author == user:
                raise ValidationError(
                    {"errors": "Нельзя подписаться на самого себя."}
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                raise ValidationError({"errors": "Вы уже подписаны."})
            serializer = FollowSerializer(
                author, context={'request': request}
            )
            Subscription.objects.create(user=user, author=author)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        if not Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError({"errors": "Подписки не существует."})
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated],
            methods=["GET"])
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True,
            context={"request": request})
        return self.get_paginated_response(serializer.data)
