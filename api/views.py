"""Views приложения api."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, F, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import DishFilter, OrderFilter
from .models import ALLOWED_TRANSITIONS, STATUS_CHOICES, Category, Dish, Favorite, Order, OrderItem, Promo, PromoCode
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .serializers import (
    AiRecommendSerializer,
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
    PromoAdminSerializer,
    PromoCodeAdminSerializer,
    PromoSerializer,
    RegisterSerializer,
    UserAdminSerializer,
    UserBanSerializer,
    UserSerializer,
)


# Авторизация

class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя по номеру телефона."""

    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    throttle_scope = 'login'

    def create(self, request, *args, **kwargs):
        """Создаёт пользователя и сразу возвращает токены (авто-вход после регистрации)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'user': UserSerializer(user, context=self.get_serializer_context()).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class CustomLoginView(generics.GenericAPIView):
    """Вход по номеру телефона и паролю. Возвращает JWT токены."""

    serializer_class = CustomLoginSerializer
    permission_classes = (AllowAny,)
    throttle_scope = 'login'

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

    queryset = Dish.objects.select_related('category').all()
    serializer_class = DishSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = DishFilter


class DishDetailView(generics.RetrieveAPIView):
    """Информация об одном блюде. Доступно всем."""

    queryset = Dish.objects.select_related('category').all()
    serializer_class = DishSerializer
    permission_classes = (AllowAny,)


class DishCreateView(generics.CreateAPIView):
    """Создание блюда. Только для админа."""

    serializer_class = DishSerializer
    permission_classes = (IsAdminOrReadOnly,)


class DishUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Обновление и удаление блюда. Только для админа."""

    queryset = Dish.objects.select_related('category').all()
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
        return Favorite.objects.select_related('dish', 'dish__category', 'user').filter(user=self.request.user)


class FavoriteCreateView(generics.CreateAPIView):
    """Добавление блюда в избранное — через сериализатор с валидацией."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """Проверяет дубликат и сохраняет с текущим пользователем."""
        dish = serializer.validated_data['dish']
        if Favorite.objects.filter(user=self.request.user, dish=dish).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'dish_id': 'Блюдо уже в избранном'})
        serializer.save(user=self.request.user)


class FavoriteDeleteView(generics.DestroyAPIView):
    """Удаление блюда из избранного."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Возвращает избранное только текущего пользователя."""
        if getattr(self, 'swagger_fake_view', False):
            return Favorite.objects.none()
        return Favorite.objects.select_related('dish', 'dish__category').filter(user=self.request.user)


# Акции

class PromoListView(generics.ListAPIView):
    """Список активных акций для главной страницы. Доступно всем."""

    serializer_class = PromoSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        """Возвращает только активные акции в нужном порядке."""
        if getattr(self, 'swagger_fake_view', False):
            return Promo.objects.none()
        return Promo.objects.select_related('dish', 'dish__category').filter(is_active=True)


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
        base = Order.objects.select_related('user', 'promo_code').prefetch_related('order_item__dish__category', 'order_item__dish')
        if self.request.user.is_staff:
            return base.all()
        return base.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    """Информация об одном заказе. Свой — клиент, любой — админ."""

    serializer_class = OrderSerializer
    permission_classes = (IsOwnerOrAdmin,)

    def get_queryset(self):
        """Клиент видит свои заказы, админ — все."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        base = Order.objects.select_related('user', 'promo_code').prefetch_related('order_item__dish__category', 'order_item__dish')
        if self.request.user.is_staff:
            return base.all()
        return base.filter(user=self.request.user)


class OrderCancelView(generics.UpdateAPIView):
    """Отмена заказа. Только владелец и только пока заказ в статусе «Создан»."""

    serializer_class = OrderSerializer
    permission_classes = (IsOwnerOrAdmin,)

    def get_queryset(self):
        """Клиент может отменить только свой заказ."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        base = Order.objects.select_related('user', 'promo_code').prefetch_related('order_item__dish')
        if self.request.user.is_staff:
            return base.all()
        return base.filter(user=self.request.user)

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
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        """Админ может менять статус любого заказа."""
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        if not self.request.user.is_staff:
            return Order.objects.none()
        return Order.objects.select_related('user', 'promo_code').prefetch_related('order_item__dish__category').all()

    def update(self, request, *args, **kwargs):
        """Устанавливает статус заказа по матрице переходов."""
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(STATUS_CHOICES):
            return Response(
                {'detail': 'Неверный статус'}, status=status.HTTP_400_BAD_REQUEST,
            )
        allowed = ALLOWED_TRANSITIONS.get(order.status, ())
        if new_status not in allowed:
            return Response(
                {'detail': f'Нельзя перевести заказ из «{order.status}» в «{new_status}». Разрешено: {list(allowed) or "-"}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = new_status
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


# AI — рекомендации блюд

class AiRecommendView(generics.GenericAPIView):
    """AI-помощник: подбор блюд по запросу (Gemini Flash + fallback)."""

    serializer_class = AiRecommendSerializer
    permission_classes = (AllowAny,)
    throttle_scope = 'ai'

    def post(self, request):
        """Принимает query, возвращает answer + dishes."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data['query']
        # Импорт тут чтобы избежать циклов
        from api.services.ai import recommend

        result = recommend(query)
        # Сериализуем dishes через DishSerializer для консистентности
        # result['dishes'] уже список dict, но лучше отдать как есть + dish_ids
        return Response(
            {
                'query': query,
                'answer': result['answer'],
                'dish_ids': result['dish_ids'],
                'dishes': result['dishes'],
                'source': result.get('source', 'fallback'),
            },
            status=status.HTTP_200_OK,
        )


# Админ — промокоды

class PromoCodeAdminListView(generics.ListAPIView):
    """Список всех промокодов (включая неактивные). Только для администратора."""

    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeAdminSerializer
    permission_classes = (IsAdminUser,)


class PromoCodeAdminCreateView(generics.CreateAPIView):
    """Создание промокода. Только для администратора."""

    serializer_class = PromoCodeAdminSerializer
    permission_classes = (IsAdminUser,)


class PromoCodeAdminEditView(generics.RetrieveUpdateDestroyAPIView):
    """Изменение и удаление промокода. Только для администратора."""

    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeAdminSerializer
    permission_classes = (IsAdminUser,)


# Админ — акции

class PromoAdminListView(generics.ListAPIView):
    """Список всех акций (включая отключённые). Только для администратора."""

    queryset = Promo.objects.select_related('dish', 'dish__category').all()
    serializer_class = PromoAdminSerializer
    permission_classes = (IsAdminUser,)


class PromoAdminCreateView(generics.CreateAPIView):
    """Создание акции. Только для администратора."""

    serializer_class = PromoAdminSerializer
    permission_classes = (IsAdminUser,)


class PromoAdminEditView(generics.RetrieveUpdateDestroyAPIView):
    """Изменение и удаление акции (включая фото). Только для администратора."""

    queryset = Promo.objects.select_related('dish', 'dish__category').all()
    serializer_class = PromoAdminSerializer
    permission_classes = (IsAdminUser,)


# Админ — категории

class CategoryEditView(generics.RetrieveUpdateDestroyAPIView):
    """Изменение и удаление категории. Только для администратора."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminUser,)

    def destroy(self, request, *args, **kwargs):
        """Не даём удалить категорию, к которой привязаны блюда."""
        category = self.get_object()
        if category.dishes.exists():
            return Response(
                {'detail': 'Сначала удали или перенеси блюда этой категории'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


# Админ — пользователи

class UserAdminListView(generics.ListAPIView):
    """Список пользователей. Только для администратора."""

    queryset = get_user_model().objects.order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = (IsAdminUser,)


class UserAdminBanView(generics.UpdateAPIView):
    """Блокировка и разблокировка пользователя (is_active). Только для администратора."""

    queryset = get_user_model().objects.all()
    serializer_class = UserBanSerializer
    permission_classes = (IsAdminUser,)

    def update(self, request, *args, **kwargs):
        """Меняет флаг is_active, запрет банить самого себя."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.get_object()
        if user == request.user:
            return Response(
                {'detail': 'Нельзя заблокировать самого себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = serializer.validated_data['is_active']
        user.save(update_fields=['is_active'])
        return Response(UserAdminSerializer(user).data, status=status.HTTP_200_OK)


# Админ — статистика

class StatsDashboardView(APIView):
    """Сводка для дэшборда: заказы и выручка за сегодня, статусы, топ блюд."""

    permission_classes = (IsAdminUser,)

    def get(self, request):
        """Собирает числа по БД: сегодня, по статусам, топ-5 блюд."""
        today = timezone.localdate()
        today_orders = Order.objects.filter(created_at__date=today)

        revenue = today_orders.exclude(status='cancelled').aggregate(
            total=Sum('total_price'),
        )['total']
        if revenue is None:
            revenue = Decimal('0')

        status_counts = {code: 0 for code, _ in STATUS_CHOICES}
        for row in Order.objects.values('status').annotate(count=Count('id')):
            status_counts[row['status']] = row['count']

        top_rows = (
            OrderItem.objects
            .values('dish__name')
            .annotate(
                qty=Sum('quantity'),
                revenue=Sum(
                    F('quantity') * F('price_at_order'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
            .order_by('-qty')[:5]
        )
        top_dishes = [
            {'name': row['dish__name'], 'qty': row['qty'] or 0, 'revenue': str(row['revenue'] or 0)}
            for row in top_rows
        ]

        return Response(
            {
                'today': {'orders': today_orders.count(), 'revenue': str(revenue)},
                'status_counts': status_counts,
                'top_dishes': top_dishes,
            },
            status=status.HTTP_200_OK,
        )
