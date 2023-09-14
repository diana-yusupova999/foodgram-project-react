from rest_framework import serializers

from config.parametrs import MIN_VALUE


def cooking_time_validator(time):
    """Метод валидации для поля cooking_time."""
    if int(time) < MIN_VALUE:
        raise serializers.ValidationError(
            "Минимальное время готовки = 1 минута"
        )
    return time
