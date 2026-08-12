"""Views приложения api."""

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import STATUS_CHOICES, Category, Dish, Favorite, Order
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .serializers import (
    CategorySerializer,
    CustomLoginSerializer,
    DishSerializer,
    FavoriteSerializer,
    LogoutSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    RegisterSerializer,
    UserSerializer,
)


# Авторизация

class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя по номеру телефона."""

    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)


class CustomLoginView(generics.GenericAPIView):
    """Вход по номеру телефона и паролю. Возвращает JWT токены."""

    serializer_class = CustomLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        """Проверяет данные и возвращает токены и данные пользователя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """Выход: добавляет refresh токен в чёрный список."""

    serializer_class = LogoutSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Помечает refresh токен как недействительный."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'detail': 'Вы вышли из системы'}, status=status.HTTP_200_OK)


# Меню

class CategoryListView(generics.ListAPIView):
    """Список всех категорий. Доступно всем."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)


class CategoryCreateView(generics.CreateAPIView):
    """Создание категории. Только для админа."""

    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)


class DishListView(generics.ListAPIView):
    """Список блюд. Доступно всем. Можно фильтровать по категории."""

    serializer_class = DishSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        """Возвращает блюда с учётом фильтра по категории."""
        queryset = Dish.objects.all()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class DishDetailView(generics.RetrieveAPIView):
    """Информация об одном блюде. Доступно всем."""

    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = (AllowAny,)


class DishCreateView(generics.CreateAPIView):
    """Создание блюда. Только для админа."""

    serializer_class = DishSerializer
    permission_classes = (IsAdminOrReadOnly,)


class DishUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Обновление и удаление блюда. Только для админа."""

    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = (IsAdminOrReadOnly,)


# Избранное

class FavoriteListView(generics.ListAPIView):
    """Список избранного текущего пользователя."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Возвращает избранное только текущего пользователя."""
        if getattr(self, 'swagger_fake_view', False):
            return Favorite.objects.none()
        return Favorite.objects.filter(user=self.request.user)


class FavoriteCreateView(generics.CreateAPIView):
    """Добавление блюда в избранное."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        """Добавляет блюдо или сообщает, если оно уже в избранном."""
        dish_id = request.data.get('dish_id')
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, dish_id=dish_id,
        )
        if not created:
            return Response(
                {'detail': 'Блюдо уже в избранном'}, status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            FavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED,
        )


class FavoriteDeleteView(generics.DestroyAPIView):
    """Удаление блюда из избранного."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Возвращает избранное только текущего пользователя."""
        if getattr(self, 'swagger_fake_view', False):
            return Favorite.objects.none()
        return Favorite.objects.filter(user=self.request.user)


# Заказы

class OrderCreateView(generics.CreateAPIView):
    """Создание нового заказа со списком блюд."""

    serializer_class = OrderCreateSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_context(self):
        """Добавляет запрос в контекст для доступа к текущему пользователю."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class OrderListView(generics.ListAPIView):
    """Список заказов. Свои заказы — клиент, все — админ."""

    serializer_class = OrderSerializer

    def get_queryset(self):
        """Клиент видит свои заказы, админ — все."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    """Информация об одном заказе. Свой — клиент, любой — админ."""

    serializer_class = OrderSerializer
    permission_classes = (IsOwnerOrAdmin,)

    def get_queryset(self):
        """Клиент видит свои заказы, админ — все."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


class OrderCancelView(generics.UpdateAPIView):
    """Отмена заказа. Только владелец и только если заказ ещё не отменён."""

    serializer_class = OrderSerializer
    permission_classes = (IsOwnerOrAdmin,)

    def get_queryset(self):
        """Клиент может отменить только свой заказ."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Меняет статус заказа на «Отменён»."""
        order = self.get_object()
        if order.status == 'cancelled':
            return Response(
                {'detail': 'Заказ уже отменён'}, status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = 'cancelled'
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Позволяет отменять заказ через POST."""
        return self.update(request, *args, **kwargs)


class OrderStatusView(generics.UpdateAPIView):
    """Смена статуса заказа. Только для администратора."""

    serializer_class = OrderSerializer

    def get_queryset(self):
        """Админ может менять статус любого заказа."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        if not self.request.user.is_staff:
            return Order.objects.none()
        return Order.objects.all()

    def update(self, request, *args, **kwargs):
        """Устанавливает статус заказа из переданного значения."""
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(STATUS_CHOICES):
            return Response(
                {'detail': 'Неверный статус'}, status=status.HTTP_400_BAD_REQUEST,
            )
        if order.status == 'cancelled':
            return Response(
                {'detail': 'Нельзя менять статус отменённого заказа'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
