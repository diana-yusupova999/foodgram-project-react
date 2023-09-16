from rest_framework import serializers

from config.parametrs import MIN_VALUE


def cooking_time_validator(time):
    """Метод валидации для поля cooking_time."""
    if int(time) < MIN_VALUE:
        raise serializers.ValidationError(
            f"Минимальное время готовки = {MIN_VALUE} минута"
        )


def amount_validator(amount):
    """Метод валидации для поля amount."""
    if int(amount) < MIN_VALUE:
        raise serializers.ValidationError(
            f"Минимальное количество ингредиентов {MIN_VALUE}"
        )
