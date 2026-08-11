"""Модели приложения api."""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# Статусы заказа
STATUS_CHOICES = (
    ('created', 'Создан'),
    ('confirmed', 'Подтверждён'),
    ('cooking', 'Готовится'),
    ('delivering', 'Доставляется'),
    ('delivered', 'Доставлен'),
    ('cancelled', 'Отменён'),
)


class User(AbstractUser):
    """Пользователь системы. Логин — номер телефона."""

    phone = PhoneNumberField('Номер телефона', unique=True, blank=True, null=True)
    photo = models.ImageField('Фото профиля', upload_to='users/', blank=True, null=True)
    address = models.CharField('Адрес доставки', max_length=255, blank=True)

    groups = models.ManyToManyField(
        'auth.Group', related_name='custom_user_set', blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', related_name='custom_user_permissions_set', blank=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Category(models.Model):
    """Категория блюд (например, «Суши», «Роллы», «Напитки»)."""

    name = models.CharField('Название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Dish(models.Model):
    """Блюдо в меню ресторана."""

    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField(
        'Цена', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='dishes',
        verbose_name='Категория',
    )
    image = models.ImageField('Фото блюда', upload_to='dishes/', blank=True, null=True)
    is_available = models.BooleanField('Доступно сейчас', default=True)

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'
        ordering = ['name']

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Избранное блюдо пользователя (любимые блюда)."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorite_item',
        verbose_name='Пользователь',
    )
    dish = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name='favorite_dish',
        verbose_name='Блюдо',
    )
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные блюда'
        unique_together = ('user', 'dish')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.dish}"


class Order(models.Model):
    """Заказ клиента."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_order',
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    status = models.CharField(
        'Статус', max_length=20, choices=STATUS_CHOICES, default='created',
    )
    delivery_address = models.CharField('Адрес доставки', max_length=255)
    total_price = models.DecimalField(
        'Итоговая сумма', max_digits=10, decimal_places=2, default=0,
    )
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ №{self.pk}"

    def calculate_total(self):
        """Пересчитывает итоговую сумму по позициям заказа."""
        total = sum(item.price_at_order * item.quantity for item in self.order_item.all())
        return total


class OrderItem(models.Model):
    """Позиция заказа (блюдо и его количество)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='order_item',
        verbose_name='Заказ',
    )
    dish = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name='dish_order_item',
        verbose_name='Блюдо',
    )
    quantity = models.PositiveIntegerField('Количество', default=1)
    price_at_order = models.DecimalField(
        'Цена на момент заказа', max_digits=10, decimal_places=2,
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f"{self.dish} × {self.quantity}"
