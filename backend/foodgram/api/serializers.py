from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.db import transaction

from config.check import is_list_empty, MIN_VALUE
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredients,
    Tag,
    User,
    Subscription
)
from .utils import recipe_ingredient_create


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = "__all__"


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed")

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class RecipeFollowSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed", "recipes_count", "recipes")

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        queryset = Recipe.objects.filter(author=obj)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeFollowSerializer(queryset, many=True).data


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source="ingredient.id",
                                            queryset=Ingredient.objects.all())
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredients
        fields = ("id", "name", "measurement_unit", "amount")
        validators = [
            UniqueTogetherValidator(
                queryset=RecipeIngredients.objects.all(),
                fields=("ingredient", "recipe")
            )
        ]


class IngredientRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.IntegerField(write_only=True, min_value=1)
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient",
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredients
        fields = ("id", "amount", "recipe")


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "author", "name", "text", "ingredients", "tags",
                  "cooking_time", "is_favorited", "is_in_shopping_cart",
                  "image")
        read_only_fields = ("id", "author",)

    def get_favorite_status(self, queryset):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return queryset.filter(user=request.user).exists()

    def get_is_favorited(self, obj):
        return self.get_favorite_status(obj.favorite_recipe)

    def get_is_in_shopping_cart(self, obj):
        return self.get_favorite_status(obj.shopping_list)

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredients.objects.filter(recipe=obj)
        return IngredientRecipeGetSerializer(recipe_ingredients,
                                             many=True).data


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ("id", "author", "name", "text", "ingredients", "tags",
                  "cooking_time", "image")
        read_only_fields = ("id", "author", "tags")

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get("ingredients")
        ingredients_list = [ingredient['id'] for ingredient in ingredients]
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                "Нельзя выбрать ингредиент более одного раза"
            )
        if is_list_empty(ingredients_list):
            raise serializers.ValidationError(
                "Рецепт не бывает без ингридиентов"
            )
        for ingredient in ingredients_list:
            if int(ingredient['amount']) < MIN_VALUE :
                raise serializers.ValidationError(
                    "Минимальное количество ингредиентов 1"
                )
        return data

    def validate_cooking_time(self, time):
        if int(time) < MIN_VALUE:
            raise serializers.ValidationError(
                "Минимальное время готовки = 1 минута"
            )
        return time

    @transaction.atomic()
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        recipe_ingredient_create(ingredients_data, RecipeIngredients, recipe)
        return recipe

    @transaction.atomic()
    def update(self, instance, validated_data):
        if "tags" in self.validated_data:
            tags_data = validated_data.pop("tags")
            instance.tags.set(tags_data)
        if "ingredients" in self.validated_data:
            ingredients_data = validated_data.pop("ingredients")
            amount_set = RecipeIngredients.objects.filter(
                recipe__id=instance.id)
            amount_set.delete()
            recipe_ingredient_create(ingredients_data, RecipeIngredients,
                                     instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        self.fields.pop("ingredients")
        self.fields.pop("tags")
        representation = super().to_representation(instance)
        representation["ingredients"] = IngredientRecipeGetSerializer(
            RecipeIngredients.objects.filter(recipe=instance), many=True
        ).data
        representation["tags"] = TagSerializer(
            instance.tags, many=True
        ).data
        return representation
