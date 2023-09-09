"""Модуль проверки авторства или административных прав API."""
from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Класс разрешения для проверки авторства или административных прав."""

    def has_permission(self, request, view):
        """Метод для проверки разрешения."""
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(
            request.user
            and (
                request.user.is_staff
                or view.get_object().author == request.user
            )
        )
