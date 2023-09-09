"""Модуль urls определяет маршруты для страниц API."""

from rest_framework.routers import DefaultRouter

from django.urls import include, path, re_path

from .views import IngredientView, RecipeView, TagView, UserView


router = DefaultRouter()
router.register(r"users", UserView)
router.register(r"tags", TagView)
router.register(r"ingredients", IngredientView, basename="ingredient")
router.register(r"recipes", RecipeView)

app_name = "api"

urlpatterns = [
    path("", include(router.urls)),
    re_path("^auth/", include("djoser.urls.authtoken")),
]
