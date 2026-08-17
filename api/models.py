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


class PromoCode(models.Model):
    """Промокод со скидкой на заказ."""

    code = models.CharField('Код', max_length=50, unique=True)
    discount_percent = models.DecimalField(
        'Скидка, %', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField('Активен', default=True)
    valid_until = models.DateField('Действует до', blank=True, null=True)
    min_order_amount = models.DecimalField(
        'Минимальная сумма заказа', max_digits=10, decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['code']

    def __str__(self):
        return self.code


class Promo(models.Model):
    """Рекламная акция на главной странице (карточка со скидкой)."""

    title = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    old_price = models.DecimalField(
        'Старая цена', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    discount_percent = models.DecimalField(
        'Скидка, %', max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    dish = models.ForeignKey(
        Dish, on_delete=models.CASCADE, related_name='promo_dish',
        verbose_name='Блюдо',
    )
    image = models.ImageField('Фото акции', upload_to='promos/', blank=True, null=True)
    is_active = models.BooleanField('Активна', default=True)
    sort_order = models.PositiveIntegerField('Порядок отображения', default=0)

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.title

    def get_new_price(self):
        """Возвращает цену со скидкой."""
        return self.old_price * (1 - self.discount_percent / 100)


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
    street = models.CharField('Улица', max_length=100)
    house = models.CharField('Дом', max_length=20)
    entrance = models.CharField('Подъезд', max_length=20, blank=True)
    floor = models.CharField('Этаж', max_length=20, blank=True)
    apartment = models.CharField('Квартира', max_length=20, blank=True)
    total_price = models.DecimalField(
        'Итоговая сумма', max_digits=10, decimal_places=2, default=0,
    )
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='promo_order', verbose_name='Промокод',
    )
    discount_amount = models.DecimalField(
        'Сумма скидки', max_digits=10, decimal_places=2, default=0,
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

    def apply_promo(self):
        """Применяет промокод и возвращает сумму скидки (0, если кода нет)."""
        if not self.promo_code:
            return 0
        discount = self.calculate_total() * self.promo_code.discount_percent / 100
        return min(discount, self.calculate_total())


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
