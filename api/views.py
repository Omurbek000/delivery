"""Views приложения api."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import DishFilter, OrderFilter
from .models import STATUS_CHOICES, Category, Dish, Favorite, Order, Promo
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .serializers import (
    CategorySerializer,
    ChangePasswordSerializer,
    ChangePhoneSerializer,
    CustomLoginSerializer,
    DishSerializer,
    FavoriteSerializer,
    LogoutSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    ProfileSerializer,
    PromoSerializer,
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


# Профиль

class ProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и редактирование своего профиля."""

    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """Возвращает профиль текущего пользователя."""
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """Смена пароля текущего пользователя."""

    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Проверяет старый пароль и сохраняет новый."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Пароль успешно изменён'}, status=status.HTTP_200_OK)


class ChangePhoneView(generics.GenericAPIView):
    """Смена номера телефона текущего пользователя."""

    serializer_class = ChangePhoneSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Проверяет номер и сохраняет его пользователю."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.phone = serializer.validated_data['phone']
        user.username = str(user.phone).replace('+', '')
        user.save()
        return Response(
            {'detail': 'Номер телефона успешно изменён'}, status=status.HTTP_200_OK,
        )


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
    """Список блюд. Доступно всем. Можно фильтровать по категории (?category=1)."""

    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = DishFilter


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


# Акции

class PromoListView(generics.ListAPIView):
    """Список активных акций для главной страницы. Доступно всем."""

    serializer_class = PromoSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        """Возвращает только активные акции в нужном порядке."""
        if getattr(self, 'swagger_fake_view', False):
            return Promo.objects.none()
        return Promo.objects.filter(is_active=True)


# Заказы

class OrderCreateView(generics.CreateAPIView):
    """Создание нового заказа со списком блюд."""

    serializer_class = OrderCreateSerializer
    permission_classes = (IsAuthenticated,)


class OrderListView(generics.ListAPIView):
    """Список заказов. Свои заказы — клиент, все — админ. Можно фильтровать по статусу (?status=confirmed)."""

    serializer_class = OrderSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = OrderFilter

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
    """Отмена заказа. Только владелец и только пока заказ в статусе «Создан»."""

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
        """Меняет статус заказа на «Отменён», если заказ ещё не принят в работу."""
        order = self.get_object()
        if order.status != 'created':
            return Response(
                {'detail': 'Заказ можно отменить только в статусе «Создан»'},
                status=status.HTTP_400_BAD_REQUEST,
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
