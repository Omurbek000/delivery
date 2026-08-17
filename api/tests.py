"""Тесты приложения api."""

from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Category, Dish, Order, Promo, PromoCode, User


class ApiTestCase(TestCase):
    """Базовый класс тестов: создаёт пользователей и клиентов."""

    def setUp(self):
        """Готовит клиентов API и пользователей для тестов."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='996555123456', phone='+996555123456',
            first_name='Али', last_name='Оморов', password='password123',
        )
        self.admin = User.objects.create_user(
            username='996555000000', phone='+996555000000',
            first_name='Админ', last_name='Админов', password='password123',
            is_staff=True,
        )
        self.category = Category.objects.create(name='Суши')
        self.dish = Dish.objects.create(
            name='Филадельфия', description='Вкусно', price='490.00',
            category=self.category,
        )

    def register(self, phone='+996555777777', password='password123'):
        """Регистрирует нового пользователя и возвращает ответ."""
        return self.client.post(
            '/register/', {'phone': phone, 'first_name': 'Гость', 'last_name': 'Гостьев', 'password': password},
        )

    def login(self, phone='+996555123456', password='password123'):
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
        self.assertEqual(response.status_code, 404)
        order.refresh_from_db()
        self.assertEqual(order.status, 'created')

    def test_change_status_by_admin(self):
        """Администратор меняет статус заказа."""
        order = Order.objects.create(user=self.user, status='created')
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/orders/{order.pk}/status/', {'status': 'delivered'})
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')

    def test_orders_list_only_own_for_client(self):
        """Клиент видит только свои заказы."""
        other = User.objects.create_user(
            username='996555999999', phone='+996555999999', password='password123',
        )
        Order.objects.create(user=self.user, status='created')
        Order.objects.create(user=other, status='created')
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/orders/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)


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
        """Новый заказ отправляет письмо администратору."""
        self.client.force_authenticate(user=self.user)
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