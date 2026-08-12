"""
URL configuration for config project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


# Настройки Swagger-документации
schema_view = get_schema_view(
    openapi.Info(
        title="Онигири — доставка еды API",  # название, видно на странице
        description="API для сервиса доставки еды с меню, заказами и избранным",  # описание
        default_version='v1',  # версия API
    ),
    public=True,  # документацию видно без авторизации
    permission_classes=(permissions.AllowAny,),  # кто может смотреть Swagger
)

# Основные маршруты проекта
urlpatterns = [
    path('admin/', admin.site.urls),  # админка: /admin/
    path('', include('api.urls')),  # все наши API-маршруты из api/urls.py
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # Swagger: /docs/
    path('accounts/', include('allauth.urls')),  # маршруты allauth (вход через соцсети)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# static(...) — в режиме разработки отдаёт загруженные медиа-файлы (картинки) по адресу /media/...