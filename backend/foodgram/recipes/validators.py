import re

from django.core.exceptions import ValidationError


def validate_username(value):
    """Метод валидации для пользователя me."""
    if value == 'me':
        raise ValidationError(
            ("Имя пользователя не может быть <me>."),
            params={"value": value},
        )
    if re.search(r'^[\w.@+-]+$', value) is None:
        raise ValidationError(
            (f"Не допустимые символы <{value}> в нике."),
            params={"value": value},
        )


def hex_color_validator(value):
    """Метод валидации для поля color."""
    if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
        raise ValidationError("Неверный цветовой HEX-код")
