from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from ..recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from ..users.models import Subscription, User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей."""

    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Метакласс регистрации пользователя."""

        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Метод для поля is_subscribed."""
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        follow = user.following.filter(author=obj)
        return follow.exists()

    def validate_password(self, password):
        """Проверяет валидность пароля."""
        validate_password(password)
        return password

    def create(self, validated_data):
        """Создает нового пользователя."""
        password = validated_data.pop('password')
        user: User = super().create(validated_data)
        try:
            user.set_password(password)
            user.save()
            return user
        except serializers.ValidationError as exc:
            user.delete()
            raise exc


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""

    current_password = serializers.CharField(
        required=True,
    )
    new_password = serializers.CharField(
        required=True,
    )

    def validate_new_password(self, value):
        """Проверяет новый пароль."""
        validate_password(value)
        return value


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Метакласс тегов."""

        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Метакласс ингредиентов."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        """Метакласс для ингредиентов в рецепте."""

        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, amount):
        """Проверка количества."""
        if amount < 0:
            raise serializers.ValidationError(
                {'errors': 'Количество ингредиента должно быть больше нуля.'}
            )
        return amount


class IngrediendAmountSerializer(serializers.ModelSerializer):
    """Сериализатор количества ингредиентов."""

    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        """Метакласс количества ингредиентов."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    recipes_count = serializers.IntegerField()
    email = serializers.EmailField(source='author.email')
    id = serializers.IntegerField(source='author.id')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        """Метакласс подписок."""

        model = Subscription
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        """Метод для поля is_subscribed."""
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        follow = user.following.filter(author=obj.author)
        return follow.exists()

    def get_recipes(self, obj) -> list[Recipe]:
        """Метод для получения списка рецептов пользователя."""
        recipes_limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)[:recipes_limit]
        serializers = RecipeSerializer(recipes, many=True)
        return serializers.data


class UserWithSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с подписками."""

    subscriptions = UserSerializer(many=True)

    class Meta:
        """Метакласс пользователя с подписками."""

        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'subscriptions',
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецепта."""

    class Meta:
        """Метакласс рецепта."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
    )

    class Meta:
        """Метакласс создания рецепта."""

        model = Recipe
        fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        """Преобразует экземпляр модели в представление для сериализации."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data

    @staticmethod
    def create_ingredients(ingredients, recipe: Recipe):
        """Создает связанные с рецептом ингредиенты в базе данных."""
        ingredients_amount = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredients_amount)

    def create(self, validated_data):
        """Создает новый рецепт на основе переданных данных."""
        ingredient = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredient, recipe)
        return recipe

    def update(self, instance: Recipe, validated_data):
        """Обновляет существующий рецепт на основе переданных данных."""
        if 'ingredients' in self.validated_data:
            ingredients = validated_data.pop('ingredients')
            RecipeIngredient.objects.filter(recipe=instance).delete()
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)

        if 'tags' in self.validated_data:
            tags = validated_data.pop('tags', instance.tags.all())
            instance.tags.set(tags)

        super().update(instance, validated_data)

        return instance


class RecipeFullSerializer(serializers.ModelSerializer):
    """Сериализатор для полной информации о рецепте."""

    tags = TagSerializer(
        many=True,
    )
    ingredients = IngrediendAmountSerializer(
        many=True,
        source='amount',
    )
    author = UserSerializer(
        read_only=True,
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Метакласс информации о рецепте."""

        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def validate_cooking_time(self, value):
        """Время приготовления больше ли 0."""
        if value < 1:
            raise serializers.ValidationError(
                {'errors': 'Время приготовления должно быть больше 0..'}
            )

    def get_is_favorited(self, obj):
        """Добавлен ли рецепт в избранное для текущего пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.in_favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Добавлен ли рецепт в корзину для текущего пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.in_carts.filter(user=request.user).exists()
