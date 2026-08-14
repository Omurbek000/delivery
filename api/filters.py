"""Фильтры приложения api."""

import django_filters

from .models import Dish, Order


class DishFilter(django_filters.FilterSet):
    """Фильтр блюд по категории."""

    class Meta:
        model = Dish
        fields = ['category']


class OrderFilter(django_filters.FilterSet):
    """Фильтр заказов по статусу."""

    class Meta:
        model = Order
        fields = ['status']
