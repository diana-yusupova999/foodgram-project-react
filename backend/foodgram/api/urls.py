from django.urls import include, path
from rest_framework import routers

from api.views import (
    TagViewSet,
    CustomUserViewSet,
    RecipeViewSet,
    IngredientViwsSet,
    ShoppingListDownloadView
)


app_name = 'api'

router = routers.DefaultRouter()
router.register("tags", TagViewSet, basename="tags")
router.register("users", CustomUserViewSet, basename="users")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("ingredients", IngredientViwsSet, basename="ingredients")

urlpatterns = [
    path("recipes/download_shopping_cart/", ShoppingListDownloadView.as_view(),
         name="download_shopping_cart"),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]
