<div align="center">

# 🍣 Онигири — Delivery API

### Доставка еды одного ресторана — от меню до статуса заказа

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white"/>
  <img src="https://img.shields.io/badge/DRF-3.16-FF1709?style=for-the-badge&logo=django&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"/>
</p>

<p>
  <img src="https://img.shields.io/badge/JWT-blacklist-000?style=flat-square&logo=jsonwebtokens&logoColor=white"/>
  <img src="https://img.shields.io/badge/tests-26_passing-10B981?style=flat-square"/>
  <img src="https://img.shields.io/badge/endpoints-22-4F8CFF?style=flat-square"/>
  <img src="https://img.shields.io/badge/models-7-8B5CF6?style=flat-square"/>
  <img src="https://img.shields.io/badge/status-production_ready-10B981?style=flat-square"/>
</p>

**Клиент смотрит меню → добавляет в избранное → оформляет адрес → отслеживает `created → delivered`**

`Category → Dish → Favorite → Order → Promo → OrderItem`

[🎬 Презентация](presentation.html) • [🎨 UI-макет](ui-mockup-main.html) • [📖 Swagger](http://127.0.0.1:8000/docs/) • [🛠️ Админка](http://127.0.0.1:8000/admin/)

</div>

---

## ✨ Что умеет

| | Возможность | Как работает | Где в коде |
|---|---|---|---|
| 📋 | **Меню** | `Category` → `Dish` (цена, фото, `is_available`) | `api/models.py:28` |
| 🔎 | **Фильтры** | `DishFilter` по `category`, `OrderFilter` по `status` (`django-filter`) | `api/filters.py:8` |
| 📄 | **Пагинация** | `PageNumberPagination` 10 на страницу, `?page_size=20` | `api/pagination.py:5` |
| ⭐ | **Избранное** | `Favorite` `unique_together(user,dish)`, `get_or_create` + защита от дубля | `api/models.py:55` `api/views.py:108` |
| 🎁 | **Промокоды** | `PromoCode` `%` + `min_order_amount` + `valid_until`, `apply_promo()` на модели | `api/models.py:76` |
| 🔥 | **Акции** | `Promo` карточка `old_price → new_price` (`get_new_price()`), `sort_order` | `api/models.py:108` |
| 🛒 | **Заказы** | `Order` + `OrderItem` (фикс `price_at_order`), `calculate_total()` | `api/models.py:142` |
| 📍 | **Адрес** | `street`+`house`+`entrance`+`floor`+`apartment` (последние 3 опционально) | `api/models.py:159` |
| 🔄 | **Статусы** | `created→confirmed→cooking→delivering→delivered` / `cancelled`, смена только админом | `api/models.py:9` `api/views.py:198` |
| 👤 | **Пользователи** | `User(AbstractUser)` логин — `phone` `PhoneNumberField` + `photo` | `api/models.py:18` |
| 🔐 | **JWT** | `register/login/logout` + `token/refresh` + `blacklist` | `api/views.py:22` |
| 🛡️ | **Права** | `IsAdminOrReadOnly` (меню), `IsOwnerOrAdmin` (заказы) | `api/permissions.py:7` |

```mermaid
flowchart LR
    A[📋 Каталог<br/>Category/Dish] --> B[⭐ Избранное<br/>Favorite]
    B --> C[🎁 Акции<br/>Promo/PromoCode]
    C --> D[🛒 Заказ<br/>Order + Items]
    D --> E[💰 Скидка<br/>apply_promo]
    E --> F[📍 Адрес<br/>street/house]
    F --> G[🔄 Статусы<br/>created→delivered]
    G --> H[✅ Готово<br/>total_price]
    style A fill:#7c3aed,stroke:#fff,color:#fff
    style D fill:#f59e0b,stroke:#fff,color:#fff
    style G fill:#059669,stroke:#fff,color:#fff
    style H fill:#111827,stroke:#fff,color:#fff
```

---

## 🧱 Стек

| | Технология | Зачем | Где |
|---|---:|---|---|
| 🐍 | **Django 5.1** | Модели, админка, `AUTH_USER_MODEL` | `config/settings.py:110` `api/models.py:18` |
| 🧩 | **DRF 3.16** | Сериализаторы, `generics` | `api/serializers.py:11` `api/views.py:1` |
| 🔐 | **SimpleJWT + blacklist** | `access/refresh`, `LogoutView` → `token.blacklist()` | `api/views.py:38` `config/settings.py:32` |
| 📞 | **PhoneNumberField** | `phone` `unique=True` `region KG` | `api/models.py:20` |
| 🔎 | **django-filter** | `DishFilter` / `OrderFilter` | `api/filters.py:1` |
| 📄 | **DRF pagination** | `StandardPagination` 10 / 100 | `api/pagination.py:5` |
| 📖 | **drf-yasg** | Swagger `/docs/` | `config/urls.py:18` |
| 🖼️ | **Pillow** | `ImageField` для `Dish.image` / `Promo.image` | `api/models.py:38` |
| 🌐 | **django-allauth + corsheaders** | Google OAuth + CORS | `config/settings.py:44` |

---

## 📦 Структура

```
delivery/
├── api/
│   ├── models.py        # User, Category, Dish, Favorite, PromoCode, Promo, Order, OrderItem + STATUS_CHOICES
│   ├── serializers.py   # вложенные read + PrimaryKeyRelated write, SerializerMethodField
│   ├── views.py         # Register/Login/Logout, Profile, Category/Dish, Favorite, Promo, Order
│   ├── urls.py          # 22 path() без DefaultRouter
│   ├── filters.py       # DishFilter / OrderFilter
│   ├── pagination.py    # StandardPagination 10
│   ├── permissions.py   # IsAdminOrReadOnly / IsOwnerOrAdmin
│   ├── admin.py         # 8 моделей в админке
│   ├── tests.py         # 26 тестов
│   └── management/commands/demo_data.py
├── config/
│   ├── settings.py      # ru-ru, Asia/Bishkek, sqlite3, JWT, allauth
│   └── urls.py          # /admin/ + /docs/ + /accounts/
├── presentation.html    # живой слайд-шоу (открыть в браузере)
├── ui-mockup-main.html  # UI-макет главной
└── requirements.txt
```

---

## 🚀 Быстрый старт — 3 команды

```powershell
git clone https://github.com/Omurbek000/delivery.git
cd delivery
copy .env.example .env  # если есть, иначе см. шаг 3
```

> Дальше — разворачиваем по шагам ниже (кликни чтобы развернуть).

<details>
<summary><b>1️⃣ Клонировать</b></summary>

```powershell
git clone https://github.com/Omurbek000/delivery.git
cd delivery
git status
git log --oneline -5
```
Файлы `presentation.html` и `ui-mockup-main.html` — открой двойным кликом в браузере.

</details>

<details>
<summary><b>2️⃣ Установить зависимости</b> — Python 3.12 + venv</summary>

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

# что внутри requirements.txt (11 пакетов)
# Django 5.1, DRF, SimpleJWT, django-filter, phonenumber_field,
# drf-yasg, Pillow, django-allauth, corsheaders, python-dotenv
```

Проверка:
```powershell
.venv\Scripts\python.exe -c "import django; print(django.VERSION)"
.venv\Scripts\python.exe manage.py check
```

</details>

<details>
<summary><b>3️⃣ Настроить .env</b></summary>

```powershell
# создай если нет .env
copy NUL .env
notepad .env
```

```ini
SECRET_KEY=django-insecure-erui)zw$8cd$a60o!((4*!og_2y)!p$8kjrx+r4e5(2(e5#8kf
DEBUG=True
ALLOWED_HOSTS=*
# для Postgres (опционально, сейчас sqlite3 для разработки):
# DATABASE_URL=postgres://delivery:delivery@localhost:5432/delivery
```

`config/settings.py:22` уже читает `.env` через `load_dotenv()`. Для старта без `.env` подставится `SECRET_KEY` по умолчанию и `sqlite3`.

</details>

<details>
<summary><b>4️⃣ Миграции + админка + демо-данные</b></summary>

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py createsuperuser  # телефон +996..., пароль 8+ символов
.venv\Scripts\python.exe manage.py demo_data  # если есть команда — зальёт Category/Dish/Promo
```

Модели: `User`, `Category`, `Dish`, `Favorite`, `PromoCode`, `Promo`, `Order`, `OrderItem` (`api/models.py:18`).

Админка: `http://127.0.0.1:8000/admin/` → `Пользователи / Категории / Блюда / Избранное / Заказы / Промокоды / Акции`

</details>

<details>
<summary><b>5️⃣ Запустить</b></summary>

```powershell
.venv\Scripts\python.exe manage.py runserver
# http://127.0.0.1:8000/docs/   → Swagger
# http://127.0.0.1:8000/admin/  → Админка
```

Проверка здоровья (если добавишь `GET /health/` — скопируй из `Service`):
```powershell
curl http://127.0.0.1:8000/docs/
```

</details>

<details>
<summary><b>6️⃣ Проверить API — примеры</b></summary>

```powershell
# Регистрация
curl -X POST http://127.0.0.1:8000/register/ -H "Content-Type: application/json" -d "{\"phone\":\"+996555123456\",\"first_name\":\"Али\",\"last_name\":\"Оморов\",\"password\":\"password123\"}"

# Вход → access/refresh
curl -X POST http://127.0.0.1:8000/login/ -H "Content-Type: application/json" -d "{\"phone\":\"+996555123456\",\"password\":\"password123\"}"
# {"user":{...},"access":"...","refresh":"..."}

# Меню (гость)
curl http://127.0.0.1:8000/dishes/
curl "http://127.0.0.1:8000/dishes/?category=1"

# Создать заказ (авторизован)
curl -X POST http://127.0.0.1:8000/orders/create/ -H "Authorization: Bearer <access>" -H "Content-Type: application/json" -d "{\"street\":\"Токтогула\",\"house\":\"100\",\"items\":[{\"dish_id\":1,\"quantity\":2}],\"promo_code\":\"Пятёрка\"}"

# Мои заказы / фильтр по статусу
curl http://127.0.0.1:8000/orders/ -H "Authorization: Bearer <access>"
curl "http://127.0.0.1:8000/orders/?status=created" -H "Authorization: Bearer <access>"
```

`Authorization: Bearer <access>` — обязательно для `/orders/`, `/favorites/`, `/profile/`.

</details>

---

## 📡 API — 22 эндпоинта

| Группа | Метод | Путь | Доступ | Описание |
|---|---|---|---|---|
| **Auth** | `POST` | `/register/` | `AllowAny` | Регистрация по `phone` |
| | `POST` | `/login/` | `AllowAny` | Вход → `access`/`refresh` |
| | `POST` | `/logout/` | `IsAuthenticated` | Blacklist `refresh` |
| | `POST` | `/token/refresh/` | `AllowAny` | Обновить `access` |
| **Профиль** | `GET/PATCH` | `/profile/` | `IsAuthenticated` | Свои данные |
| | `POST` | `/profile/password/` | `IsAuthenticated` | Смена пароля |
| | `POST` | `/profile/phone/` | `IsAuthenticated` | Смена телефона |
| **Меню** | `GET` | `/categories/` | `AllowAny` | Список категорий |
| | `POST` | `/categories/create/` | `IsAdmin` | Создать категорию |
| | `GET` | `/dishes/` | `AllowAny` | Блюда + `?category=1` |
| | `GET` | `/dishes/<id>/` | `AllowAny` | Одно блюдо |
| | `POST` | `/dishes/create/` | `IsAdmin` | Создать блюдо |
| | `PUT/PATCH/DELETE` | `/dishes/<id>/edit/` | `IsAdmin` | Изменить/удалить |
| **Акции** | `GET` | `/promo/` | `AllowAny` | Активные `Promo` по `sort_order` |
| **Избранное** | `GET` | `/favorites/` | `IsAuthenticated` | Моё избранное |
| | `POST` | `/favorites/create/` | `IsAuthenticated` | Добавить (`dish_id`) |
| | `DELETE` | `/favorites/<id>/delete/` | `IsAuthenticated` | Удалить |
| **Заказы** | `POST` | `/orders/create/` | `IsAuthenticated` | Создать с `items[]` + `promo_code` |
| | `GET` | `/orders/` | `IsAuthenticated` | Свои (админ — все) + `?status=` |
| | `GET` | `/orders/<id>/` | `IsOwnerOrAdmin` | Детали |
| | `PATCH` | `/orders/<id>/cancel/` | `IsOwnerOrAdmin` | Отмена только `created` |
| | `PATCH` | `/orders/<id>/status/` | `IsAdmin` | Смена статуса |

Swagger: `http://127.0.0.1:8000/docs/` (`config/urls.py:28`), ReDoc также доступен.

---

## 🔐 Роли и права

| Роль | Что может |
|---|---|
| **Гость** | `GET /categories/`, `GET /dishes/`, `GET /promo/` |
| **Клиент** | `+ /favorites/`, `/orders/create/`, `/orders/` (только свои), `/profile/` |
| **Админ** (`is_staff`) | Всё + `POST /categories/create`, `POST /dishes/create`, `PATCH /orders/<id>/status/` (любой заказ) |

Фильтры как в `user-backend-style`: `DjangoFilterBackend` + `filterset_class` (`api/filters.py:8`), пагинация `PageNumberPagination 10` (`api/pagination.py:5`).

---

## 🧪 Тесты — 26

```powershell
.venv\Scripts\python.exe manage.py test api.tests --verbosity=2
```

| Класс | Что проверяет |
|---|---|
| `AuthTests` | `register` 201, короткий пароль 400, `login` → tokens, неверный пароль 400 |
| `MenuTests` | `categories/` 200 для гостя, `dishes/` 200, фильтр `?category=`, создание только для админа 403 |
| `OrderTests` | создание 201 + `total_price` 980.00, пустые `items` 400, отмена только `created`, смена статуса только админ, `orders/` только свои |
| `FavoriteTests` | добавление 201, дубль 400 |
| `PromoCodeTests` | применение скидки, `min_order_amount`, `valid_until` |

Запуск одного класса:
```powershell
.venv\Scripts\python.exe manage.py test api.tests.OrderTests --verbosity=2
```

---

## 📸 Презентация

* `presentation.html` — слайды (открой в браузере, стрелки ← →, `F` — fullscreen)
* `ui-mockup-main.html` — макет главной (карточки `Promo`, меню, корзина)

Оба файла уже в корне репо — работают без сервера (`file://`).

---

## 🛠️ Админка

`http://127.0.0.1:8000/admin/` — 8 моделей: `User` (phone), `Category`, `Dish`, `Favorite`, `Order`, `OrderItem`, `PromoCode`, `Promo` (`api/admin.py:8`).

Полезно: `DishAdmin` фильтры по `category`/`is_available`, `OrderAdmin` по `status`.

---

## 📝 Примечания

* **Один ресторан, не агрегатор** — архитектура под одно заведение (нет `Restaurant` модели).
* **Телефон — логин** — `username = phone.replace('+','')` (`api/serializers.py:94`).
* **Цена фиксируется** — `OrderItem.price_at_order` сохраняет цену на момент заказа, не меняется при изменении `Dish.price`.
* **Скидка считается на модели** — `Order.calculate_total()` + `Order.apply_promo()` (`api/models.py:174`), не в сериализаторе.
* **SQLite для dev**, готов к `PostgreSQL` (замени `DATABASES` в `config/settings.py:52`).
