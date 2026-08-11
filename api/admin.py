"""Настройка админ-панели приложения api."""

from django.contrib import admin

from .models import Category, Dish, Favorite, Order, OrderItem, User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    """Админка пользователей."""

    list_display = ('phone', 'first_name', 'last_name', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка категорий блюд."""

    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    """Админка блюд."""

    list_display = ('name', 'price', 'category', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка избранного."""

    list_display = ('user', 'dish', 'created_at')
    list_filter = ('user',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка заказов."""

    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__phone', 'delivery_address')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Админка позиций заказа."""

    list_display = ('order', 'dish', 'quantity', 'price_at_order')
