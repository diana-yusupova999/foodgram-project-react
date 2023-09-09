from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)
from users.fields import ImageBase64Field
from users.serializers import UserGetSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeTagSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='tag.id')
    name = serializers.ReadOnlyField(source='tag.name')
    color = serializers.ReadOnlyField(source='tag.color')
    slug = serializers.ReadOnlyField(source='tag.slug')

    class Meta:
        model = RecipeTag
        fields = ('id', 'name', 'color', 'slug')
        validators = [UniqueTogetherValidator(
            queryset=RecipeTag.objects.all, fields=['recipe', 'tag']
        )]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [UniqueTogetherValidator(
            queryset=RecipeIngredient.objects.all,
            fields=['recipe', 'ingredient']
        )]


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = ImageBase64Field(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        extra_kwargs = {'user': {'write_only': True},
                        'recipe': {'write_only': True}}

    def validate(self, data):
        if Favorite.objects.filter(
                user=data['user'], recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError('Уже в избранном')
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = ImageBase64Field(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        extra_kwargs = {'user': {'write_only': True},
                        'recipe': {'write_only': True}}

    def validate(self, data):
        if ShoppingCart.objects.filter(
                user=data['user'], recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError('Уже в списке покупок')
        return data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserGetSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = ImageBase64Field(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return False if user.is_anonymous else Recipe.objects.filter(
            favorites__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return False if user.is_anonymous else Recipe.objects.filter(
            cart__user=user, id=obj.id).exists()

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError('Минимальное время приготовления'
                                              ' минута')
        return value

    def validate(self, data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')

        if not tags or len(tags) < 1:
            raise serializers.ValidationError('Необходим минимум один тег')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Тег уже существует')
        for tag in tags:
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError(f'Тега с id {tag} не '
                                                  'существует')

        if not ingredients or len(ingredients) < 1:
            raise serializers.ValidationError('Необходим минимум один '
                                              'ингридиент')
        unique_ingredients = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            ingredient_amount = int(ingredient['amount'])
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError('Ингридиента с id '
                                                  f'{ingredient_id} не '
                                                  'существует')
            if ingredient_id in unique_ingredients:
                raise serializers.ValidationError('Ингредиент уже существует')
            if ingredient_amount < 1:
                raise serializers.ValidationError('Минимальное количество 1')
            unique_ingredients.append(ingredient_id)

        data['tags'] = tags
        data['ingredients'] = ingredients
        return data

    def create_recipe_tags(self, recipe, tags):
        temp = []
        for tag in tags:
            if RecipeTag.objects.filter(recipe=recipe, tag_id=tag).exists():
                continue
            temp.append(RecipeTag(recipe=recipe, tag_id=tag))
        RecipeTag.objects.bulk_create(temp, batch_size=10)

    def create_recipe_ingredients(self, recipe, ingredients):
        temp = []
        for ingredient in ingredients:
            if RecipeIngredient.objects.filter(
                    recipe=recipe,
                    ingredient_id=ingredient.get('id'),
                    amount=ingredient.get('amount')
            ).exists():
                continue
            temp.append(RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount')
            ))
        RecipeIngredient.objects.bulk_create(temp, batch_size=10)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.create_recipe_tags(recipe, tags)
        self.create_recipe_ingredients(recipe, ingredients)
        return recipe

    def update(self, obj, validated_data):
        if 'tags' in self.initial_data:
            tags = validated_data.pop('tags')
            obj.tags.clear()
            self.create_recipe_tags(obj, tags)
        if 'ingredients' in self.initial_data:
            ingredients = validated_data.pop('ingredients')
            obj.ingredients.clear()
            self.create_recipe_ingredients(obj, ingredients)
        return super().update(obj, validated_data)
