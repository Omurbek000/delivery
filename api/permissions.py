"""Права доступа приложения api."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Чтение разрешено всем, изменение — только администратору.

    Пример: меню. Гость смотрит блюда, создавать/менять может только админ.
    """

    def has_permission(self, request, view):
        """Разрешает чтение всем, изменение — только сотрудникам."""
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    """Доступ к объекту — только его владельцу или администратору.

    Пример: заказ. Клиент видит свой заказ, админ — любой.
    """

    def has_object_permission(self, request, view, obj):
        """Разрешает доступ владельцу объекта и администратору."""
        if request.user.is_staff:
            return True
        return obj.user == request.user
