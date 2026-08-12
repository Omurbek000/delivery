"""Сериализаторы приложения api."""

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Dish, Favorite, Order, OrderItem, User


# Пользователи и авторизация

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для отображения."""

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'photo', 'address')


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор регистрации нового пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        """Создаёт пользователя, хешируя пароль через set_password."""
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
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

    class Meta:
        model = Order
        fields = (
            'id', 'user', 'created_at', 'status', 'delivery_address',
            'total_price', 'comment', 'order_item',
        )


class OrderItemCreateSerializer(serializers.Serializer):
    """Сериализатор позиции при создании заказа."""

    dish_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания заказа со списком блюд."""

    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ('delivery_address', 'comment', 'items')

    def validate_items(self, items):
        """Проверяет, что все блюда существуют и доступны."""
        if not items:
            raise serializers.ValidationError('Заказ не может быть пустым')
        dish_ids = [item['dish_id'] for item in items]
        dishes = Dish.objects.filter(id__in=dish_ids, is_available=True)
        if len(dishes) != len(set(dish_ids)):
            raise serializers.ValidationError('Некоторые блюда недоступны')
        return items

    def create(self, validated_data):
        """Создаёт заказ, позиции и пересчитывает итоговую сумму."""
        items_data = validated_data.pop('items')
        order = Order.objects.create(
            user=self.context['request'].user, **validated_data,
        )
        for item_data in items_data:
            dish = Dish.objects.get(pk=item_data['dish_id'])
            OrderItem.objects.create(
                order=order, dish=dish, quantity=item_data['quantity'],
                price_at_order=dish.price,
            )
        order.total_price = order.calculate_total()
        order.save()
        return order

    def to_representation(self, instance):
        """Возвращает заказ полностью — со статусом, суммой и позициями."""
        return OrderSerializer(instance).data
