"""Сериализаторы приложения api."""

from datetime import date

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Dish, Favorite, Order, OrderItem, Promo, PromoCode, User


# Пользователи и авторизация

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для отображения."""

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'photo')


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля: просмотр и редактирование своих данных."""

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'photo')


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        """Проверяет, что новый пароль не слишком короткий."""
        if len(value) < 8:
            raise serializers.ValidationError('Пароль должен быть не короче 8 символов')
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
        """Проверяет, что пароль не слишком короткий."""
        if len(value) < 8:
            raise serializers.ValidationError('Пароль должен быть не короче 8 символов')
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
        """Проверяет refresh токен и помещает его в чёрный список."""
        try:
            token = RefreshToken(value)
            token.blacklist()
        except Exception:
            raise serializers.ValidationError('Неверный или уже использованный токен')
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
            'id', 'name', 'description', 'price', 'image', 'is_available',
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
    quantity = serializers.IntegerField(min_value=1)


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
        dishes = Dish.objects.filter(id__in=dish_ids, is_available=True)
        if len(dishes) != len(set(dish_ids)):
            raise serializers.ValidationError('Некоторые блюда недоступны')
        return items

    def validate_promo_code(self, value):
        """Находит промокод и проверяет, что он действует."""
        promo = PromoCode.objects.filter(code__iexact=value).first()
        if not promo:
            raise serializers.ValidationError('Промокод не найден')
        if not promo.is_active:
            raise serializers.ValidationError('Промокод не активен')
        if promo.valid_until and promo.valid_until < date.today():
            raise serializers.ValidationError('Срок действия промокода истёк')
        return promo

    def create(self, validated_data):
        """Создаёт заказ, позиции и пересчитывает итоговую сумму со скидкой."""
        items_data = validated_data.pop('items')
        promo = validated_data.pop('promo_code', None)
        order = Order.objects.create(
            user=self.context['request'].user, promo_code=promo, **validated_data,
        )
        for item_data in items_data:
            dish = Dish.objects.get(pk=item_data['dish_id'])
            OrderItem.objects.create(
                order=order, dish=dish, quantity=item_data['quantity'],
                price_at_order=dish.price,
            )
        subtotal = order.calculate_total()
        if promo and subtotal < promo.min_order_amount:
            raise serializers.ValidationError(
                f'Минимальная сумма заказа для этого промокода — {promo.min_order_amount}'
            )
        order.discount_amount = order.apply_promo()
        order.total_price = subtotal - order.discount_amount
        order.save()
        return order

    def to_representation(self, instance):
        """Возвращает заказ полностью — со статусом, суммой и позициями."""
        return OrderSerializer(instance).data
