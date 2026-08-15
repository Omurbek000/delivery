"""Демо-данные для ресторана «Онигири»."""

from django.core.management.base import BaseCommand

from api.models import Category, Dish, PromoCode


class Command(BaseCommand):
    """Заполняет базу категориями, блюдами и промокодом для демонстрации."""

    help = 'Заполняет базу демо-данными: категории, блюда и промокод ресторана «Онигири»'

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

        self.stdout.write(self.style.SUCCESS(f'Готово: создано {created} новых блюд'))
        if promo_created:
            self.stdout.write(self.style.SUCCESS(f'Промокод «{promo.code}» создан (скидка {promo.discount_percent}%)'))
        else:
            self.stdout.write(f'Промокод «{promo.code}» уже существует')
