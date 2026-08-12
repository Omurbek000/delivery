"""Маршруты приложения api."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from . import views

urlpatterns = [
    # Авторизация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Меню
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('dishes/', views.DishListView.as_view(), name='dish-list'),
    path('dishes/<int:pk>/', views.DishDetailView.as_view(), name='dish-detail'),
    path('dishes/create/', views.DishCreateView.as_view(), name='dish-create'),
    path('dishes/<int:pk>/edit/', views.DishUpdateDeleteView.as_view(), name='dish-edit'),

    # Избранное
    path('favorites/', views.FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/create/', views.FavoriteCreateView.as_view(), name='favorite-create'),
    path('favorites/<int:pk>/delete/', views.FavoriteDeleteView.as_view(), name='favorite-delete'),

    # Заказы
    path('orders/create/', views.OrderCreateView.as_view(), name='order-create'),
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', views.OrderCancelView.as_view(), name='order-cancel'),
    path('orders/<int:pk>/status/', views.OrderStatusView.as_view(), name='order-status'),
]
