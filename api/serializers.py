"""Сериализаторы приложения api."""

from collections import Counter
from datetime import date
from decimal import Decimal

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Dish, Favorite, Order, OrderItem, Promo, PromoCode, User


# Пользователи и авторизация

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для отображения."""

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'photo', 'is_staff')


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля: просмотр и редактирование своих данных.

    Телефон менять нельзя (read_only) — только через отдельный эндпоинт
    /profile/phone/, где есть проверка на занятость номера.
    """

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'photo')
        extra_kwargs = {'phone': {'read_only': True}}


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        """Проверяет новый пароль валидаторами Django (длина, частые пароли).

        Валидаторы из settings.AUTH_PASSWORD_VALIDATORS + проверка на
        похожесть с данными текущего пользователя.
        """
        try:
            password_validation.validate_password(value, user=self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError('; '.join(e.messages))
        return value

    def validate(self, attrs):
        """Проверяет, что старый пароль введён верно."""
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError('Старый пароль введён неверно')
        return attrs


class ChangePhoneSerializer(serializers.Serializer):
    """Сериализатор смены номера телефона."""

    phone = PhoneNumberField()

    def validate_phone(self, value):
        """Проверяет, что номер свободен и не занят другим пользователем."""
        user = self.context['request'].user
        if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Этот номер уже занят другим пользователем')
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации нового пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'password')

    def validate_password(self, value):
        """Проверяет пароль валидаторами Django (длина, частые пароли)."""
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError('; '.join(e.messages))
        return value

    def create(self, validated_data):
        """Создаёт пользователя, хешируя пароль через set_password."""
        password = validated_data.pop('password')
        user = User.objects.create(
            username=str(validated_data['phone']).replace('+', ''),
            **validated_data,
        )
        user.set_password(password)
        user.save()
        return user


class CustomLoginSerializer(serializers.Serializer):
    """Сериализатор входа по номеру телефона и паролю."""

    phone = PhoneNumberField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Проверяет номер телефона и пароль, сохраняет пользователя."""
        user = User.objects.filter(phone=attrs['phone']).first()
        if not user or not user.check_password(attrs['password']):
            raise serializers.ValidationError('Неверный номер телефона или пароль')
        if not user.is_active:
            raise serializers.ValidationError('Пользователь заблокирован')
        self.user = user
        return attrs

    def to_representation(self, instance):
        """Возвращает пользователя и JWT токены."""
        refresh = RefreshToken.for_user(self.user)
        return {
            'user': UserSerializer(self.user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class LogoutSerializer(serializers.Serializer):
    """Сериализатор выхода: принимает refresh токен для чёрного списка."""

    refresh = serializers.CharField()

    def validate_refresh(self, value):
        """Проверяет refresh токен и помещает его в чёрный список.

        Токен должен быть корректным и принадлежать текущему пользователю —
        иначе кто-то мог бы разлогинить чужого пользователя.
        """
        try:
            token = RefreshToken(value)
        except Exception:
            raise serializers.ValidationError('Неверный или уже использованный токен')
        # user_id в токене может прийти строкой — сравниваем через str()
        token_user_id = str(token.payload.get('user_id', ''))
        if token_user_id != str(self.context['request'].user.pk):
            raise serializers.ValidationError('Можно выйти только с собственного токена')
        token.blacklist()
        return value


# Меню

class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории блюд."""

    class Meta:
        model = Category
        fields = ('id', 'name')


class DishSerializer(serializers.ModelSerializer):
    """Сериализатор блюда."""

    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True, source='category',
    )

    class Meta:
        model = Dish
        fields = (
            'id', 'name', 'description', 'ingredients', 'price', 'image', 'is_available',
            'category', 'category_id',
        )


# Избранное

class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного блюда."""

    dish = DishSerializer(read_only=True)
    dish_id = serializers.PrimaryKeyRelatedField(
        queryset=Dish.objects.all(), write_only=True, source='dish',
    )

    class Meta:
        model = Favorite
        fields = ('id', 'dish', 'dish_id', 'created_at')


# Акции

class PromoSerializer(serializers.ModelSerializer):
    """Сериализатор акции главной страницы."""

    dish = DishSerializer(read_only=True)
    new_price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Promo
        fields = (
            'id', 'title', 'description', 'old_price', 'new_price',
            'discount_percent', 'dish', 'image', 'sort_order',
        )

    def get_new_price(self, obj):
        """Возвращает цену со скидкой."""
        return obj.get_new_price()

    def get_image(self, obj):
        """Возвращает фото акции, а если его нет — фото блюда."""
        image = obj.image or obj.dish.image
        if image:
            return image.url
        return None


# Заказы

class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор позиции заказа для отображения."""

    dish = DishSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'dish', 'quantity', 'price_at_order')


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор заказа для отображения."""

    order_item = OrderItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'user', 'created_at', 'status',
            'street', 'house', 'entrance', 'floor', 'apartment',
            'total_price', 'discount_amount', 'subtotal', 'promo_code', 'comment', 'order_item',
        )

    def get_subtotal(self, obj):
        """Возвращает сумму без учёта скидки."""
        return obj.calculate_total()


class OrderItemCreateSerializer(serializers.Serializer):
    """Сериализатор позиции при создании заказа."""

    dish_id = serializers.IntegerField()
    # Максимум 99 шт одного блюда — защита от переполнения итоговой суммы в БД
    quantity = serializers.IntegerField(min_value=1, max_value=99)


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания заказа со списком блюд и промокодом."""

    items = OrderItemCreateSerializer(many=True, write_only=True)
    promo_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = ('street', 'house', 'entrance', 'floor', 'apartment', 'comment', 'items', 'promo_code')

    def validate_items(self, items):
        """Проверяет, что все блюда существуют и доступны."""
        if not items:
            raise serializers.ValidationError('Заказ не может быть пустым')
        dish_ids = [item['dish_id'] for item in items]
        unique_ids = set(dish_ids)
        dishes = Dish.objects.filter(id__in=unique_ids, is_available=True)
        # Сравниваем по уникальным id — дубликаты в заказе разрешены (склеим в create)
        if dishes.count() != len(unique_ids):
            raise serializers.ValidationError('Некоторые блюда недоступны')
        return items

    def validate_promo_code(self, value):
        """Находит промокод и проверяет, что он действует. Пустая строка — значит без промокода."""
        if not value:
            return None
        promo = PromoCode.objects.filter(code__iexact=value).first()
        if not promo:
            raise serializers.ValidationError('Промокод не найден')
        if not promo.is_active:
            raise serializers.ValidationError('Промокод не активен')
        if promo.valid_until and promo.valid_until < date.today():
            raise serializers.ValidationError('Срок действия промокода истёк')
        return promo

    def create(self, validated_data):
        """Создаёт заказ атомарно: bulk_create, склейка дубликатов, проверка min_order_amount внутри транзакции."""
        items_data = validated_data.pop('items')
        promo = validated_data.pop('promo_code', None)

        # Склеиваем дубликаты dish_id -> суммируем quantity
        merged = Counter()
        for item in items_data:
            merged[item['dish_id']] += item['quantity']

        with transaction.atomic():
            order = Order.objects.create(
                user=self.context['request'].user, promo_code=promo, **validated_data,
            )
            # Один запрос вместо N
            dishes = Dish.objects.filter(id__in=merged.keys()).in_bulk()
            bulk_items = [
                OrderItem(
                    order=order,
                    dish=dishes[dish_id],
                    quantity=qty,
                    price_at_order=dishes[dish_id].price,
                )
                for dish_id, qty in merged.items()
            ]
            OrderItem.objects.bulk_create(bulk_items)

            # Пересчитываем без лишних запросов — уже знаем цены
            subtotal = sum(item.price_at_order * item.quantity for item in bulk_items)
            if promo and subtotal < promo.min_order_amount:
                raise serializers.ValidationError(
                    f'Минимальная сумма заказа для этого промокода — {promo.min_order_amount}'
                )
            # apply_promo использует calculate_total(), но мы уже посчитали subtotal
            if promo:
                discount = subtotal * promo.discount_percent / Decimal('100')
                discount = min(discount, subtotal)
            else:
                discount = Decimal('0')
            order.discount_amount = discount
            order.total_price = subtotal - discount
            order.save(update_fields=['discount_amount', 'total_price'])
            return order

    def to_representation(self, instance):
        """Возвращает заказ полностью — со статусом, суммой и позициями."""
        return OrderSerializer(instance).data


# Админ — промокоды, акции, пользователи

class PromoCodeAdminSerializer(serializers.ModelSerializer):
    """Промокод для админ-панели: полный CRUD."""

    class Meta:
        model = PromoCode
        fields = ('id', 'code', 'discount_percent', 'is_active', 'valid_until', 'min_order_amount')

    def validate_code(self, value):
        """Код не может быть пустым, лишние пробелы убираем."""
        if not value.strip():
            raise serializers.ValidationError('Код не может быть пустым')
        return value.strip()


class PromoAdminSerializer(serializers.ModelSerializer):
    """Акция для админ-панели: полный CRUD с выбором блюда и загрузкой фото."""

    dish_id = serializers.PrimaryKeyRelatedField(
        queryset=Dish.objects.all(), write_only=True, source='dish',
    )
    dish = DishSerializer(read_only=True)

    class Meta:
        model = Promo
        fields = (
            'id', 'title', 'description', 'old_price', 'discount_percent',
            'dish', 'dish_id', 'image', 'is_active', 'sort_order',
        )


class UserAdminSerializer(serializers.ModelSerializer):
    """Пользователь для админ-панели: список. Менять можно только is_active."""

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'photo', 'is_active', 'is_staff', 'date_joined')
        read_only_fields = ('id', 'phone', 'first_name', 'last_name', 'photo', 'is_staff', 'date_joined')


class UserBanSerializer(serializers.Serializer):
    """Тумблер блокировки пользователя."""

    is_active = serializers.BooleanField()


# AI — рекомендации

class AiRecommendSerializer(serializers.Serializer):
    """Сериализатор запроса к AI-помощнику."""

    query = serializers.CharField(required=True, allow_blank=False, max_length=500)

