"""Тесты приложения api."""

from decimal import Decimal

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Category, Dish, Order, OrderItem, Promo, PromoCode, User


class ApiTestCase(TestCase):
    """Базовый класс тестов: создаёт пользователей и клиентов."""

    def setUp(self):
        """Готовит клиентов API и пользователей для тестов."""
        self.client = APIClient()
        # Сбрасываем кэш троттлинга, чтобы тесты не упирались в лимит 5/мин
        cache.clear()
        self.user = User.objects.create_user(
            username='996555123456', phone='+996555123456',
            first_name='Али', last_name='Оморов', password='StroNG-Secret2026',
        )
        self.admin = User.objects.create_user(
            username='996555000000', phone='+996555000000',
            first_name='Админ', last_name='Админов', password='StroNG-Secret2026',
            is_staff=True,
        )
        self.category = Category.objects.create(name='Суши')
        self.dish = Dish.objects.create(
            name='Филадельфия', description='Вкусно', price='490.00',
            category=self.category,
        )

    def register(self, phone='+996555777777', password='StroNG-Secret2026'):
        """Регистрирует нового пользователя и возвращает ответ."""
        return self.client.post(
            '/register/', {'phone': phone, 'first_name': 'Гость', 'last_name': 'Гостьев', 'password': password},
        )

    def login(self, phone='+996555123456', password='StroNG-Secret2026'):
        """Выполняет вход и возвращает ответ с токенами."""
        return self.client.post('/login/', {'phone': phone, 'password': password})


class AuthTests(ApiTestCase):
    """Тесты регистрации и входа."""

    def test_register_new_user(self):
        """Регистрация нового пользователя создаёт аккаунт."""
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(phone='+996555777777').exists())

    def test_register_short_password_fails(self):
        """Регистрация с коротким паролем отклоняется."""
        response = self.register(password='123')
        self.assertEqual(response.status_code, 400)

    def test_login_returns_tokens(self):
        """Вход возвращает access и refresh токены."""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password_fails(self):
        """Вход с неверным паролем отклоняется."""
        response = self.login(password='wrongpass')
        self.assertEqual(response.status_code, 400)

    def test_register_common_password_fails(self):
        """Регистрация с частым паролем (password123) отклоняется валидаторами Django."""
        response = self.register(password='password123')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(phone='+996555777777').exists())

    def test_logout_strangers_refresh_token_rejected(self):
        """Нельзя разлогинить чужого пользователя с его refresh токеном."""
        login_response = self.login()
        refresh = login_response.data['refresh']
        # Другой пользователь пытается выйти с чужим токеном
        another = User.objects.create_user(
            username='996555888888', phone='+996555888888',
            first_name='Бек', last_name='Беков', password='StroNG-Secret2026',
        )
        self.client.force_authenticate(user=another)
        response = self.client.post('/logout/', {'refresh': refresh})
        self.assertEqual(response.status_code, 400)
        # Свой токен по-прежнему работает: его можно обновить
        self.client.force_authenticate(user=self.user)
        refresh_response = self.client.post('/token/refresh/', {'refresh': refresh})
        self.assertEqual(refresh_response.status_code, 200)

    def test_logout_own_refresh_token_blacklists(self):
        """Свой refresh токен при выходе уходит в чёрный список."""
        login_response = self.login()
        refresh = login_response.data['refresh']
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/logout/', {'refresh': refresh})
        self.assertEqual(response.status_code, 200)
        # После выхода токен не работает
        refresh_response = self.client.post('/token/refresh/', {'refresh': refresh})
        self.assertEqual(refresh_response.status_code, 401)


class MenuTests(ApiTestCase):
    """Тесты просмотра меню."""

    def test_category_list_visible_for_guest(self):
        """Список категорий виден без авторизации."""
        response = self.client.get('/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_dish_list_visible_for_guest(self):
        """Список блюд виден без авторизации."""
        response = self.client.get('/dishes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_dish_filter_by_category(self):
        """Фильтр блюд по категории работает."""
        response = self.client.get(f'/dishes/?category={self.category.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_dish_create_only_for_admin(self):
        """Создание блюда доступно только администратору."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/dishes/create/', {'name': 'Ролл', 'price': '100.00', 'category_id': self.category.pk},
        )
        self.assertEqual(response.status_code, 403)


class OrderTests(ApiTestCase):
    """Тесты заказов."""

    def make_order(self, user, quantity=2):
        """Создаёт заказ от имени пользователя."""
        self.client.force_authenticate(user=user)
        return self.client.post('/orders/create/', {
            'street': 'Токтогула',
            'house': '100',
            'items': [{'dish_id': self.dish.pk, 'quantity': quantity}],
        }, format='json')

    def test_create_order_available_for_client(self):
        """Клиент может создать заказ."""
        response = self.make_order(self.user)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')
        self.assertEqual(response.data['total_price'], '980.00')

    def test_create_order_empty_items_fails(self):
        """Заказ без блюд отклоняется."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/orders/create/', {
            'street': 'Токтогула', 'house': '100', 'items': [],
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_create_order_quantity_over_limit_fails(self):
        """Слишком большое количество одного блюда отклоняется (максимум 99)."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/orders/create/', {
            'street': 'Токтогула', 'house': '100',
            'items': [{'dish_id': self.dish.pk, 'quantity': 100}],
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_create_order_comment_too_long_fails(self):
        """Комментарий длиннее 500 символов отклоняется."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/orders/create/', {
            'street': 'Токтогула', 'house': '100',
            'comment': 'х' * 600,
            'items': [{'dish_id': self.dish.pk, 'quantity': 1}],
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cancel_order_only_in_created_status(self):
        """Отменить заказ можно только в статусе «Создан»."""
        order = Order.objects.create(user=self.user, status='confirmed')
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/orders/{order.pk}/cancel/')
        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')

    def test_change_status_only_for_admin(self):
        """Менять статус заказа может только администратор."""
        order = Order.objects.create(user=self.user, status='created')
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/orders/{order.pk}/status/', {'status': 'confirmed'})
        # Явное разрешение IsAdminUser — честный 403 Forbidden без утечек
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, 'created')

    def test_change_status_by_admin(self):
        """Администратор меняет статус заказа по разрешенному переходу."""
        order = Order.objects.create(user=self.user, status='created')
        self.client.force_authenticate(user=self.admin)
        # created -> confirmed разрешен (см. ALLOWED_TRANSITIONS)
        response = self.client.patch(f'/orders/{order.pk}/status/', {'status': 'confirmed'})
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')
        # Проверка что неверный прыжок created -> delivered теперь 400
        order2 = Order.objects.create(user=self.user, status='created')
        response2 = self.client.patch(f'/orders/{order2.pk}/status/', {'status': 'delivered'})
        self.assertEqual(response2.status_code, 400)

    def test_orders_list_only_own_for_client(self):
        """Клиент видит только свои заказы."""
        other = User.objects.create_user(
            username='996555999999', phone='+996555999999', password='StroNG-Secret2026',
        )
        Order.objects.create(user=self.user, status='created')
        Order.objects.create(user=other, status='created')
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)


class ProfileTests(ApiTestCase):
    """Тесты профиля и его ограничений."""

    def test_profile_phone_cannot_be_changed(self):
        """Телефон через /profile/ сменить нельзя (read_only) — защита от дубликатов."""
        another = User.objects.create_user(
            username='996555888888', phone='+996555888888',
            first_name='Бек', last_name='Беков', password='StroNG-Secret2026',
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.patch('/profile/', {'phone': '+996555888888'})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, '+996555123456')
        self.assertEqual(another.phone, '+996555888888')


class FavoriteTests(ApiTestCase):
    """Тесты избранного."""

    def test_add_dish_to_favorites(self):
        """Клиент добавляет блюдо в избранное."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/favorites/create/', {'dish_id': self.dish.pk})
        self.assertEqual(response.status_code, 201)

    def test_duplicate_favorite_fails(self):
        """Повторное добавление того же блюда отклоняется."""
        self.client.force_authenticate(user=self.user)
        self.client.post('/favorites/create/', {'dish_id': self.dish.pk})
        response = self.client.post('/favorites/create/', {'dish_id': self.dish.pk})
        self.assertEqual(response.status_code, 400)


class PromoCodeTests(ApiTestCase):
    """Тесты промокодов."""

    def make_promo(self, code='Пятёрка', discount='20.00', **kwargs):
        """Создаёт промокод и возвращает его."""
        return PromoCode.objects.create(code=code, discount_percent=discount, **kwargs)

    def make_order(self, code=None):
        """Создаёт заказ от имени пользователя с промокодом (если передан)."""
        self.client.force_authenticate(user=self.user)
        data = {
            'street': 'Токтогула',
            'house': '100',
            'items': [{'dish_id': self.dish.pk, 'quantity': 2}],
        }
        if code is not None:
            data['promo_code'] = code
        return self.client.post('/orders/create/', data, format='json')

    def test_order_with_promo_gets_discount(self):
        """Заказ со скидкой 20%: subtotal 980, total 784, discount 196."""
        self.make_promo()
        response = self.make_order(code='Пятёрка')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['subtotal'], Decimal('980.00'))
        self.assertEqual(response.data['discount_amount'], '196.00')
        self.assertEqual(response.data['total_price'], '784.00')

    def test_order_with_unknown_promo_fails(self):
        """Несуществующий промокод отклоняется."""
        response = self.make_order(code='Секрет')
        self.assertEqual(response.status_code, 400)

    def test_order_with_inactive_promo_fails(self):
        """Неактивный промокод отклоняется."""
        self.make_promo(is_active=False)
        response = self.make_order(code='Пятёрка')
        self.assertEqual(response.status_code, 400)

    def test_order_with_below_min_amount_fails(self):
        """Заказ меньше минимальной суммы для промокода отклоняется."""
        self.make_promo(min_order_amount='1000.00')
        response = self.make_order(code='Пятёрка')
        self.assertEqual(response.status_code, 400)

    def test_order_without_promo_no_discount(self):
        """Заказ без промокода — скидка 0, сумма без изменений."""
        response = self.make_order()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['discount_amount'], '0.00')
        self.assertEqual(response.data['total_price'], '980.00')


class EmailTests(ApiTestCase):
    """Тесты уведомлений о новых заказах."""

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST_USER='onigiri@mail.ru',
        ADMIN_EMAIL='admin@onigiri.delivery',
    )
    def test_new_order_sends_email_to_admin(self):
        """Новый заказ отправляет письмо администратору (через on_commit)."""
        self.client.force_authenticate(user=self.user)
        # on_commit в тестах срабатывает только внутри captureOnCommitCallbacks
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/orders/create/', {
                'street': 'Токтогула',
                'house': '100',
                'items': [{'dish_id': self.dish.pk, 'quantity': 2}],
            }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Новый заказ', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['admin@onigiri.delivery'])

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST_USER='',
        ADMIN_EMAIL='admin@onigiri.delivery',
    )
    def test_no_email_when_mail_not_configured(self):
        """Без почтового ящика письмо не отправляется."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/orders/create/', {
            'street': 'Токтогула',
            'house': '100',
            'items': [{'dish_id': self.dish.pk, 'quantity': 2}],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 0)


class PromoTests(ApiTestCase):
    """Тесты акций главной страницы."""

    def make_promo(self, title='Филадельфия', **kwargs):
        """Создаёт акцию и возвращает объект."""
        defaults = {'old_price': '490.00', 'discount_percent': '20.00'}
        defaults.update(kwargs)
        return Promo.objects.create(title=title, dish=self.dish, **defaults)

    def test_promo_list_shows_active(self):
        """Активная акция попадает в список на главной."""
        self.make_promo(title='Филадельфия')
        response = self.client.get('/promo/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Филадельфия')

    def test_promo_list_hides_inactive(self):
        """Неактивные акции не показываются."""
        self.make_promo(title='Скрытая', is_active=False)
        response = self.client.get('/promo/')
        self.assertEqual(response.data['results'], [])

    def test_promo_has_dish_and_new_price(self):
        """Акция возвращает цену со скидкой и вложенное блюдо."""
        self.make_promo(title='Калифорния', old_price='450.00', discount_percent='15.00')
        response = self.client.get('/promo/')
        promo = response.data['results'][0]
        self.assertEqual(promo['old_price'], '450.00')
        self.assertEqual(promo['new_price'], Decimal('382.50'))
        self.assertEqual(promo['dish']['name'], 'Филадельфия')


class AiRecommendTests(ApiTestCase):
    """Тесты AI-подбора блюд (/ai/recommend/)."""

    AI_OFF = {
        'OPENCODE_API_KEY': '',
        'GEMINI_API_KEY': '',
    }

    def make_dish(self, name, ingredients='', **kwargs):
        """Создаёт блюдо и возвращает его."""
        defaults = {'description': 'Вкусно', 'price': '100.00', 'category': self.category}
        defaults.update(kwargs)
        return Dish.objects.create(name=name, ingredients=ingredients, **defaults)

    def test_recommend_empty_query_fails(self):
        """Пустой запрос отклоняется валидацией."""
        response = self.client.post('/ai/recommend/', {'query': ''}, format='json')
        self.assertEqual(response.status_code, 400)

    @override_settings(**AI_OFF)
    def test_recommend_fallback_without_keys(self):
        """Без API-ключей эндпоинт не падает — работает rule-based fallback."""
        response = self.client.post(
            '/ai/recommend/', {'query': 'какие самые вкусные'}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['source'], 'fallback')
        self.assertTrue(response.data['dishes'])
        self.assertIn(response.data['dishes'][0]['id'], {d.pk for d in Dish.objects.all()})

    @override_settings(**AI_OFF)
    def test_recommend_no_cheese_filter(self):
        """Запрос «без сыра» не предлагает блюда с сыром в составе."""
        cheese_dish = self.make_dish('Чиз-ролл', ingredients='рис, сыр, лосось')
        plain_dish = self.make_dish('Огуречный', ingredients='рис, огурец')
        response = self.client.post('/ai/recommend/', {'query': 'найди что-то без сыра'}, format='json')
        self.assertEqual(response.status_code, 200)
        ids = response.data['dish_ids']
        self.assertIn(plain_dish.pk, ids)
        self.assertNotIn(cheese_dish.pk, ids)


class AdminApiTests(ApiTestCase):
    """Тесты админ-API: промокоды, акции, категории, юзеры, статистика."""

    def admin_client(self):
        """Переключает клиент на администратора и возвращает его."""
        self.client.force_authenticate(user=self.admin)
        return self.client

    def test_promocode_list_create_only_admin(self):
        """Промокоды видит и создаёт только админ; гость — 401, клиент — 403."""
        PromoCode.objects.create(code='Скидка10', discount_percent='10.00')
        self.assertEqual(self.client.get('/promo-codes/').status_code, 401)
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get('/promo-codes/').status_code, 403)
        client = self.admin_client()
        self.assertEqual(client.get('/promo-codes/').status_code, 200)
        create = client.post(
            '/promo-codes/create/',
            {'code': 'Лето', 'discount_percent': '15.00', 'min_order_amount': '100.00'},
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        self.assertTrue(PromoCode.objects.filter(code='Лето', discount_percent=Decimal('15.00')).exists())

    def test_promocode_edit_and_delete(self):
        """Админ меняет и удаляет промокод."""
        promo = PromoCode.objects.create(code='Пять', discount_percent='5.00')
        client = self.admin_client()
        patch = client.patch(f'/promo-codes/{promo.pk}/edit/', {'is_active': False}, format='json')
        self.assertEqual(patch.status_code, 200)
        promo.refresh_from_db()
        self.assertFalse(promo.is_active)
        self.assertEqual(client.delete(f'/promo-codes/{promo.pk}/edit/').status_code, 204)
        self.assertFalse(PromoCode.objects.filter(code='Пять').exists())

    def test_promo_create_with_dish(self):
        """Админ создаёт акцию с привязкой к блюду."""
        client = self.admin_client()
        create = client.post(
            '/promos/create/',
            {
                'title': 'Хит', 'old_price': '490.00', 'discount_percent': '10.00',
                'dish_id': self.dish.pk, 'sort_order': 9,
            },
            format='json',
        )
        self.assertEqual(create.status_code, 201)
        self.assertEqual(create.data['dish']['name'], 'Филадельфия')
        self.assertTrue(Promo.objects.filter(title='Хит').exists())

    def test_promo_list_all_for_admin(self):
        """Админ видит все акции, включая отключённые."""
        Promo.objects.create(
            title='Отключённая', old_price='150.00', discount_percent='10.00',
            dish=self.dish, is_active=False,
        )
        response = self.admin_client().get('/promos/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_category_delete_guarded(self):
        """Категорию с блюдами удалить нельзя, пустую можно."""
        client = self.admin_client()
        empty = Category.objects.create(name='Пустая')
        self.assertEqual(client.delete(f'/categories/{empty.pk}/edit/').status_code, 204)
        self.assertFalse(Category.objects.filter(name='Пустая').exists())
        response = client.delete(f'/categories/{self.category.pk}/edit/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_users_list_and_ban(self):
        """Админ смотрит пользователей и банит; забаненный не может войти."""
        other = User.objects.create_user(
            username='996555888888', phone='+996555888888',
            first_name='Бек', last_name='Беков', password='StroNG-Secret2026',
        )
        client = self.admin_client()
        users = client.get('/users/')
        self.assertEqual(users.status_code, 200)
        self.assertEqual(users.data['count'], 3)
        ban = client.patch(f'/users/{other.pk}/ban/', {'is_active': False}, format='json')
        self.assertEqual(ban.status_code, 200)
        other.refresh_from_db()
        self.assertFalse(other.is_active)
        self.client.force_authenticate(user=None)
        login = self.client.post('/login/', {'phone': '+996555888888', 'password': 'StroNG-Secret2026'})
        self.assertEqual(login.status_code, 400)

    def test_admin_cannot_ban_self(self):
        """Администратор не может заблокировать самого себя."""
        client = self.admin_client()
        response = client.patch(f'/users/{self.admin.pk}/ban/', {'is_active': False}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_users_api_forbidden_for_client(self):
        """Обычный (нестафф) пользователь не видит список юзеров и статистику."""
        self.client.force_authenticate(user=self.user)
        self.assertEqual(self.client.get('/users/').status_code, 403)
        self.assertEqual(self.client.get('/stats/').status_code, 403)

    def test_stats_dashboard_numbers(self):
        """Статистика считает заказы за сегодня, выручку без отменённых и топ блюд."""
        order = Order.objects.create(user=self.user, status='confirmed', total_price=Decimal('980.00'))
        OrderItem.objects.create(
            order=order, dish=self.dish, quantity=2, price_at_order=Decimal('490.00'),
        )
        Order.objects.create(user=self.user, status='cancelled', total_price=Decimal('100.00'))
        data = self.admin_client().get('/stats/').data
        self.assertEqual(data['today']['orders'], 2)
        self.assertEqual(Decimal(data['today']['revenue']), Decimal('980.00'))
        self.assertEqual(data['status_counts']['confirmed'], 1)
        self.assertEqual(data['status_counts']['cancelled'], 1)
        self.assertEqual(data['top_dishes'][0]['name'], 'Филадельфия')
        self.assertEqual(data['top_dishes'][0]['qty'], 2)
        self.assertEqual(Decimal(data['top_dishes'][0]['revenue']), Decimal('980.00'))