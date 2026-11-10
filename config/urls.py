"""
URL configuration for config project.
"""
from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Папка со сборкой админ-панели (создаётся командой npm run build в admin/)
ADMIN_DIST = Path(__file__).resolve().parent.parent / 'admin' / 'dist'

# Папка со сборкой витрины сайта (создаётся командой npm run build в site/)
SITE_DIST = Path(__file__).resolve().parent.parent / 'site' / 'dist'


def admin_panel(request, sp_path=''):
    """Раздаёт собранную админ-панель по /panel/.

    Сам HTML грузится свободно: вход защищает логин в интерфейсе,
    а данные всё равно отдаются только staff-пользователю через API.
    """
    requested = (ADMIN_DIST / sp_path).resolve()
    # Защита от выхода за пределы папки (../ и т.п.)
    if requested != ADMIN_DIST and ADMIN_DIST not in requested.parents:
        raise Http404
    if not requested.is_file():
        requested = ADMIN_DIST / 'index.html'  # SPA: любой путь ведёт на приложение
    if not requested.is_file():
        raise Http404('Сначала собери админ-панель: запуск npm run build в папке admin/')
    return FileResponse(requested.open('rb'))

def site_spa(request, sp_path=''):
    """Раздаёт собранную витрину сайта по корню (/) — любой путь ведёт на SPA."""
    requested = (SITE_DIST / sp_path).resolve()
    # Защита от выхода за пределы папки (../ и т.п.)
    if requested != SITE_DIST and SITE_DIST not in requested.parents:
        raise Http404
    if not requested.is_file():
        requested = SITE_DIST / 'index.html'  # SPA: все пути отдаёт react-router
    if not requested.is_file():
        raise Http404('Сначала собери сайт: запуск npm run build в папке site/')
    return FileResponse(requested.open('rb'))


# Настройки Swagger-документации
schema_view = get_schema_view(
    openapi.Info(
        title="Онигири — доставка еды API",  # название, видно на странице
        description="API для сервиса доставки еды с меню, заказами и избранным",  # описание
        default_version='v1',  # версия API
    ),
    public=settings.DEBUG,  # в prod схема доступна только администратору
    # Открыто всем в dev; в prod — только staff
    permission_classes=(permissions.AllowAny if settings.DEBUG else permissions.IsAdminUser,),
)

# Основные маршруты проекта
urlpatterns = [
    path('admin/', admin.site.urls),  # админка: /admin/
    path('', include('api.urls')),  # все 23 эндпоинта API (ключ /api/v1/ вернём при появлении v2)
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # Swagger: /docs/
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # ReDoc: /redoc/
    path('accounts/', include('allauth.urls')),  # маршруты allauth (вход через соцсети)
    # Собранная админ-панель (Vite) — HTML и её статика
    path('panel/', admin_panel, name='admin-panel'),
    path('panel/<path:sp_path>', admin_panel, name='admin-panel-files'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# static(...) — в режиме разработки отдаёт загруженные медиа-файлы (картинки) по адресу /media/...

# Витрина сайта (Vite) в самом конце: API, админка, panel, docs и media важнее.
urlpatterns += [
    path('', site_spa, name='site-root'),
    path('<path:sp_path>', site_spa, name='site-spa'),
]
