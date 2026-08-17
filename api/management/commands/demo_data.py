"""Демо-данные для ресторана «Онигири»."""

from django.core.management.base import BaseCommand

from api.models import Category, Dish, Promo, PromoCode


class Command(BaseCommand):
    """Заполняет базу категориями, блюдами, акциями и промокодом для демонстрации."""

    help = 'Заполняет базу демо-данными: категории, блюда, акции и промокод ресторана «Онигири»'

    def handle(self, *args, **options):
        """Создаёт категории и блюда, если их ещё нет."""
        categories = {
            'Суши': [
                {'name': 'Филадельфия', 'description': 'Лосось, сливочный сыр, авокадо', 'price': '490.00'},
                {'name': 'Калифорния', 'description': 'Краб, авокадо, икра тобико', 'price': '450.00'},
                {'name': 'Спайси тунец', 'description': 'Тунец, острый соус, рис', 'price': '520.00'},
            ],
            'Роллы': [
                {'name': 'Ролл с лососем', 'description': 'Лосось, огурец, рис', 'price': '380.00'},
                {'name': 'Ролл с угрём', 'description': 'Угорь, огурец, соус унаги', 'price': '420.00'},
                {'name': 'Хот-ролл', 'description': 'Запечённый ролл с лососем и сыром', 'price': '550.00'},
            ],
            'Напитки': [
                {'name': 'Зелёный чай', 'description': 'Горячий зелёный чай', 'price': '120.00'},
                {'name': 'Кола', 'description': 'Кола 0.33 л', 'price': '150.00'},
                {'name': 'Сок манго', 'description': 'Манговый нектар 0.33 л', 'price': '180.00'},
            ],
            'Добавки': [
                {'name': 'Имбирь', 'description': 'Маринованный имбирь', 'price': '90.00'},
                {'name': 'Васаби', 'description': 'Острый васаби', 'price': '80.00'},
                {'name': 'Соевый соус', 'description': 'Соевый соус', 'price': '70.00'},
            ],
        }

        created = 0
        for category_name, dishes in categories.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for dish_data in dishes:
                _, was_created = Dish.objects.get_or_create(
                    name=dish_data['name'],
                    defaults={
                        'description': dish_data['description'],
                        'price': dish_data['price'],
                        'category': category,
                    },
                )
                if was_created:
                    created += 1

        promo, promo_created = PromoCode.objects.get_or_create(
            code='Пятёрка', defaults={'discount_percent': '20.00'},
        )

        promos = [
            {'title': 'Филадельфия', 'description': 'Лосось, сливочный сыр, авокадо · 8 шт', 'dish': 'Филадельфия', 'old_price': '490.00', 'discount_percent': '20.00', 'sort_order': 1},
            {'title': 'Хот-ролл', 'description': 'Запечённый, с лососем и сыром · 8 шт', 'dish': 'Хот-ролл', 'old_price': '550.00', 'discount_percent': '15.00', 'sort_order': 2},
            {'title': 'Калифорния', 'description': 'Краб, авокадо, икра тобико · 8 шт', 'dish': 'Калифорния', 'old_price': '450.00', 'discount_percent': '15.00', 'sort_order': 3},
            {'title': 'Спайси тунец', 'description': 'Тунец, острый соус, рис · 8 шт', 'dish': 'Спайси тунец', 'old_price': '520.00', 'discount_percent': '12.00', 'sort_order': 4},
            {'title': 'Ролл с лососем', 'description': 'Лосось, огурец, рис · 8 шт', 'dish': 'Ролл с лососем', 'old_price': '380.00', 'discount_percent': '10.00', 'sort_order': 5},
            {'title': 'Ролл с угрём', 'description': 'Угорь, огурец, соус унаги · 8 шт', 'dish': 'Ролл с угрём', 'old_price': '420.00', 'discount_percent': '10.00', 'sort_order': 6},
        ]

        promo_created_count = 0
        for promo_data in promos:
            dish = Dish.objects.get(name=promo_data['dish'])
            _, was_created = Promo.objects.get_or_create(
                title=promo_data['title'],
                defaults={
                    'description': promo_data['description'],
                    'old_price': promo_data['old_price'],
                    'discount_percent': promo_data['discount_percent'],
                    'dish': dish,
                    'sort_order': promo_data['sort_order'],
                },
            )
            if was_created:
                promo_created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Готово: создано {created} новых блюд'))
        self.stdout.write(self.style.SUCCESS(f'Создано {promo_created_count} новых акций'))
        if promo_created:
            self.stdout.write(self.style.SUCCESS(f'Промокод «{promo.code}» создан (скидка {promo.discount_percent}%)'))
        else:
            self.stdout.write(f'Промокод «{promo.code}» уже существует')
