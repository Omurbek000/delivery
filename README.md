<div align="center">

<img src="https://img.shields.io/badge/🍣-Онигири--Delivery--API-ff3e6c?style=for-the-badge" alt="Онигири"/>

# 🍣 Онигири — Delivery API

**Доставка еды одного ресторана — от меню до статуса заказа**

`Клиент смотрит меню → добавляет в избранное → оформляет адрес → отслеживает заказ до статуса delivered`

<p align="center">
  <a href="#-быстрый-старт--3-команды">🚀 Быстрый старт</a>&nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="#-api--23-эндпоинта">📡 API</a>&nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="#-docker">🐳 Docker</a>&nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="presentation.html">🎬 Презентация</a>&nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="ui-mockup-main.html">🎨 UI-макет</a>
</p>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1-092E20?style=flat-square&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.16-FF1709?style=flat-square&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
<br>
![JWT blacklist](https://img.shields.io/badge/JWT-blacklist-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-/docs-85EA2D?style=flat-square&logo=swagger&logoColor=black)
![tests](https://img.shields.io/badge/tests-44_passing-10B981?style=flat-square)
![endpoints](https://img.shields.io/badge/endpoints-33-4F8CFF?style=flat-square)
![models](https://img.shields.io/badge/models-8-8B5CF6?style=flat-square)
![status](https://img.shields.io/badge/production-ready-10B981?style=flat-square)
![license](https://img.shields.io/badge/license-MIT-F6D51F?style=flat-square)

</div>


---

## 📑 Содержание

| | Раздел |
|---|---|
| ✨ | [Что умеет](#-что-умеет) |
| 🧱 | [Стек](#-стек) |
| 🗺️ | [Структура проекта](#-структура) |
| 📦 | [Данные и модели](#-данные-и-модели) |
| 🐳 | [Docker](#-docker) |
| 🚀 | [Быстрый старт](#-быстрый-старт--3-команды) |
| 📡 | [API — 33 эндпоинта](#-api--33-эндпоинта) |
| 🔐 | [Роли и права](#-роли-и-права) |
| 🧪 | [Тесты — 44](#-тесты--44) |
| 🎬 | [Презентация](#-презентация) |
| 🛠️ | [Админка](#-админка) |
| 🖥️ | [Админ-панель](#%EF%B8%8F-админ-панель-react) |
| 📝 | [Примечания](#-примечания) |

---

## ✨ Что умеет

| | Возможность | Как работает | Где в коде |
|---|---|---|---|
| 📋 | **Меню** | `Category` → `Dish` (цена, фото, `is_available`) | `api/models.py:28` |
| 🔎 | **Фильтры** | `DishFilter` по `category`, `OrderFilter` по `status` (`django-filter`) | `api/filters.py:8` |
| 📄 | **Пагинация** | `PageNumberPagination` 10 на страницу, `?page_size=20` | `api/pagination.py:5` |
| ⭐ | **Избранное** | `Favorite` `unique_together(user,dish)`, защита от дубля | `api/views.py:108` |
| 🎁 | **Промокоды** | `PromoCode` `%` + `min_order_amount` + `valid_until`, `apply_promo()` на модели | `api/models.py:76` |
| 🔥 | **Акции** | `Promo` карточка `old_price → new_price` (`get_new_price()`), `sort_order` | `api/models.py:108` |
| 🛒 | **Заказы** | `Order` + `OrderItem` (фикс `price_at_order`), `calculate_total()` | `api/models.py:142` |
| 📍 | **Адрес** | `street`+`house`+`entrance`+`floor`+`apartment` (последние 3 опционально) | `api/models.py:159` |
| 🔄 | **Статусы** | `created→confirmed→cooking→delivering→delivered / cancelled`, по матрице переходов | `api/models.py:9` `api/views.py:198` |
| ✉️ | **Уведомления** | Письмо админу о новом заказе (`on_commit`, smtp) | `api/signals.py:13` |
| 🤖 | **AI-подбор** | Рекомендации блюд: opencode → gemini → groq → rule-fallback + кэш | `api/services/ai.py` |
| 👤 | **Пользователи** | `User(AbstractUser)` логин — `phone` `PhoneNumberField` + `photo` | `api/models.py:18` |
| 🔐 | **JWT** | `register/login/logout` + `token/refresh` + `blacklist` | `api/views.py:22` |
| 🛡️ | **Права** | `IsAdminOrReadOnly` (меню), `IsOwnerOrAdmin` (заказы) | `api/permissions.py:7` |

```mermaid
flowchart LR
    A[📋 Каталог<br/>Category / Dish] --> B[⭐ Избранное<br/>Favorite]
    B --> C[🎁 Акции<br/>Promo / PromoCode]
    C --> D[🛒 Заказ<br/>Order + OrderItem]
    D --> E[💰 Скидка<br/>apply_promo]
    E --> F[📍 Адрес<br/>street / house]
    F --> G[🔄 Статусы<br/>created → delivered]
    G --> H[✅ Готово<br/>total_price]
    A ~~~ M[🤖 AI-подбор<br/>/ai/recommend/]
    M ~~~ D
    style A fill:#7c3aed,stroke:#fff,color:#fff
    style D fill:#f59e0b,stroke:#fff,color:#fff
    style G fill:#059669,stroke:#fff,color:#fff
    style H fill:#111827,stroke:#fff,color:#fff
    style M fill:#ec4899,stroke:#fff,color:#fff
```

---

## 🧱 Стек

| | Технология | Зачем | Где |
|---|---|---|---|
| 🐍 | **Django 5.1** | Модели, админка, `AUTH_USER_MODEL` | `config/settings.py:181` |
| 🧩 | **DRF 3.16** | Сериализаторы, `generics` | `api/serializers.py` `api/views.py` |
| 🔐 | **SimpleJWT + blacklist** | `access/refresh`, `LogoutView` → `token.blacklist()` | `config/settings.py:61` |
| 📞 | **PhoneNumberField** | `phone` `unique=True` `region KG` | `api/models.py:20` |
| 🔎 | **django-filter** | `DishFilter` / `OrderFilter` | `api/filters.py` |
| 📄 | **DRF pagination** | `StandardPagination` 10 / 100 | `api/pagination.py` |
| 📖 | **drf-yasg** | Swagger `/docs/` + ReDoc | `config/urls.py` |
| 🖼️ | **Pillow** | `ImageField` для `Dish.image` / `Promo.image` | `api/models.py:38` |
| 🌐 | **django-allauth + corsheaders** | Google OAuth + CORS | `config/settings.py:67` |
| ⚪ | **Whitenoise** | Статика в проде без nginx | `config/settings.py:77` |
| 🔴 | **Redis (опционально)** | Общий кэш AI + throttling между воркерами | `config/settings.py:333` |
| 🐬 | **PostgreSQL 18** | Основная БД, `DATABASE_URL` из `.env` | `config/settings.py:121` |

---

## 🗺️ Структура

```
delivery/
├── api/
│   ├── models.py        # User, Category, Dish, Favorite, PromoCode, Promo, Order, OrderItem + STATUS_CHOICES
│   ├── serializers.py   # вложенные read + PrimaryKeyRelated write, SerializerMethodField
│   ├── views.py         # Register/Login/Logout, Profile, Category/Dish, Favorite, Promo, Order, AI
│   ├── urls.py          # 33 path() без DefaultRouter (+ схема без дублей)
│   ├── filters.py       # DishFilter / OrderFilter
│   ├── pagination.py    # StandardPagination 10
│   ├── permissions.py   # IsAdminOrReadOnly / IsOwnerOrAdmin
│   ├── admin.py         # 8 моделей в админке
│   ├── tests.py         # 44 теста
│   ├── services/ai.py   # AI-подбор блюд: opencode → gemini → groq → fallback + кэш
│   ├── signals.py       # email админу о новом заказе (transaction.on_commit)
│   └── management/commands/demo_data.py
├── admin/               # админ-панель: React + Vite + TanStack Query (дев: npm run dev, прод: /panel/)
├── config/
│   ├── settings.py      # ru-ru, Asia/Bishkek, Postgres через DATABASE_URL (или sqlite3), JWT, allauth, whitenoise
│   └── urls.py          # /admin/ + /panel/ + /docs/ + /accounts/
├── Dockerfile           # multi-stage + collectstatic (Whitenoise)
├── docker-compose.yml   # postgres:18 + redis + web (порты наружу только на 127.0.0.1)
├── presentation.html    # живой слайд-шоу (открыть в браузере)
├── ui-mockup-main.html  # UI-макет главной
└── requirements.txt
```

---

## 📦 Данные и модели

> `User → Favorite → Dish → Category` и `User → Order → OrderItem → Dish` + `Promo`/`PromoCode`

| Модель | Суть | Ключевые поля |
|---|---|---|
| `User` | Пользователь, вход по `phone` (+996) | `phone (unique)`, `photo` |
| `Category` | Категория меню | `name (unique)` |
| `Dish` | Блюдо | `price (Decimal)`, `image`, `ingredients`, `is_available` |
| `Favorite` | Избранное пользователя | `unique_together (user, dish)` |
| `PromoCode` | Скидка на заказ | `discount_percent`, `min_order_amount`, `valid_until` |
| `Promo` | Акция на главной | `old_price`, `get_new_price()`, `sort_order` |
| `Order` | Заказ клиента | `status`, адрес из 5 полей, `total_price`, `discount_amount` |
| `OrderItem` | Позиция заказа | `quantity`, `price_at_order` (цена фиксируется) |

> [!NOTE]
> `OrderItem.dish → on_delete=PROTECT`: блюдо, которое есть в заказах, удалить нельзя — история покупателей защищена.

**Жизненный цикл заказа** (`api/models.py:22`):

```
created ──► confirmed ──► cooking ──► delivering ──► delivered
   │                                                  (финиш)
   ▼
cancelled  (доступно клиенту только из «created»)
```
Матрица переходов живёт в `ALLOWED_TRANSITIONS` — API не даёт перепрыгивать статусы.

---

## 🐳 Docker

<details open>
<summary><b>Поднимаем всё одной командой</b></summary>

```powershell
docker compose up -d --build
# ▶ http://127.0.0.1:8000/docs/  — Swagger
# ▶ http://127.0.0.1:8000/admin/ — Админка
```

| Контейнер | Что внутри |
|---|---|
| `web` | Django + gunicorn (3 воркера), авто-`migrate`, `demo_data` |
| `db` | `postgres:18-alpine`, юзер `admin/admin`, база `delivery` |
| `redis` | `redis:7-alpine` — общий кэш AI + throttling |

> [!CAUTION]
> В compose БД и Redis светятся только на `127.0.0.1` (`docker-compose.yml`) — на сервере не открывай их наружу.

</details>

---

## 🚀 Быстрый старт — 3 команды

```powershell
git clone https://github.com/Omurbek000/delivery.git
cd delivery
copy .env.example .env   # впиши SECRET_KEY/DEBUG/DATABASE_URL
```

> Дальше — по шагам (кликни, чтобы развернуть).

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

# основные зависимости
# Django 5.1 · DRF · SimpleJWT · django-filter · phonenumber-field
# drf-yasg · Pillow · django-allauth · corsheaders · whitenoise · redis · psycopg2
```

Проверка:
```powershell
.venv\Scripts\python.exe manage.py check
```

</details>

<details>
<summary><b>3️⃣ Настроить .env</b></summary>

```powershell
copy NUL .env
notepad .env
```

```ini
SECRET_KEY=django-insecure-erui)zw$8cd$a60o!((4*!og_2y)!p$8kjrx+r4e5(2(e5#8kf
DEBUG=True
ALLOWED_HOSTS=*
# PostgreSQL (если задан — Django работает на нем, база delivery):
DATABASE_URL=postgres://admin:admin@localhost:5432/delivery
# Redis для общего кэша (пусто — LocMem):
REDIS_URL=
```

> [!WARNING]
> На сервере `DEBUG=False` обязательно и `DATABASE_URL` с другим, сложным паролем. Если `DEBUG` не задан — по умолчанию `False` (безопасно), но не подставится dev-ключ `SECRET_KEY` и сервер не поднимется без `.env`.

</details>

<details>
<summary><b>4️⃣ Миграции + админка + демо-данные</b></summary>

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py createsuperuser  # телефон +996..., пароль 8+ символов
.venv\Scripts\python.exe manage.py demo_data        # зальёт Category/Dish/Promo
```

Админка: `http://127.0.0.1:8000/admin/` → `Пользователи / Категории / Блюда / Избранное / Заказы / Промокоды / Акции`

</details>

<details>
<summary><b>5️⃣ Запустить</b></summary>

```powershell
.venv\Scripts\python.exe manage.py runserver
# http://127.0.0.1:8000/docs/   → Swagger
# http://127.0.0.1:8000/admin/  → Админка
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

# AI-подбор блюд
curl -X POST http://127.0.0.1:8000/ai/recommend/ -H "Content-Type: application/json" -d "{\"query\":\"вкусное без сыра\"}"

# Создать заказ (авторизован)
curl -X POST http://127.0.0.1:8000/orders/create/ -H "Authorization: Bearer <access>" -H "Content-Type: application/json" -d "{\"street\":\"Токтогула\",\"house\":\"100\",\"items\":[{\"dish_id\":1,\"quantity\":2}],\"promo_code\":\"Пятёрка\"}"

# Мои заказы / фильтр по статусу
curl http://127.0.0.1:8000/orders/ -H "Authorization: Bearer <access>"
curl "http://127.0.0.1:8000/orders/?status=created" -H "Authorization: Bearer <access>"
```

`Authorization: Bearer <access>` — обязательно для `/orders/`, `/favorites/`, `/profile/`.

</details>

---

## 📡 API — 33 эндпоинта

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
| **AI** | `POST` | `/ai/recommend/` | `AllowAny` | Подбор блюд по запросу (LLM + fallback) |
| **Админ-промокоды** | `GET/POST` | `/promo-codes/`, `/promo-codes/create/` | `IsAdmin` | Список / создание |
| | `PATCH/DELETE` | `/promo-codes/<id>/edit/` | `IsAdmin` | Изменить / удалить |
| **Админ-акции** | `GET/POST` | `/promos/`, `/promos/create/` | `IsAdmin` | Все акции, включая отключённые |
| | `PATCH/DELETE` | `/promos/<id>/edit/` | `IsAdmin` | Изменить (и фото) / удалить |
| **Админ-категории** | `PATCH/DELETE` | `/categories/<id>/edit/` | `IsAdmin` | Переименовать; удаление нельзя, если есть блюда |
| **Админ-юзеры** | `GET` | `/users/` | `IsAdmin` | Список пользователей |
| | `PATCH` | `/users/<id>/ban/` | `IsAdmin` | Бан/разбан (`is_active`), себя — нельзя |
| **Дэшборд** | `GET` | `/stats/` | `IsAdmin` | Заказы/выручка за сегодня, статусы, топ-5 блюд |

Swagger: `http://127.0.0.1:8000/docs/`, ReDoc: `http://127.0.0.1:8000/redoc/` — 33 эндпоинта без дублей.

---

## 🔐 Роли и права

| Роль | Что может |
|---|---|
| **Гость** | `GET /categories/`, `GET /dishes/`, `GET /promo/`, `POST /ai/recommend/` |
| **Клиент** | `+ /favorites/`, `/orders/create/`, `/orders/` (только свои), `/profile/` |
| **Админ** (`is_staff`) | Всё + `POST /categories/create`, `POST /dishes/*`, `PATCH /orders/<id>/status/` (любой заказ) |

Пагинация `PageNumberPagination 10` (`api/pagination.py:5`), фильтры `DjangoFilterBackend` (`api/filters.py:8`), throttling: `login 5/min`, `anon 20/min`, `user 60/min`, `ai 30/min` (`config/settings.py`).

---

## 🧪 Тесты — 44

```powershell
.venv\Scripts\python.exe manage.py test api.tests --verbosity=2
```

| Класс | Что проверяет |
|---|---|
| `AuthTests` | `register` 201, короткий пароль 400, `login` → токены, неверный пароль 400 |
| `MenuTests` | `categories/` 200 гостю, `dishes/` 200, фильтр `?category=`, создание только админом 403 |
| `OrderTests` | создание 201 + `total_price` 980.00, пустые `items` 400, отмена только в `created`, смена статуса только админ, `orders/` — только свои |
| `FavoriteTests` | добавление 201, дубль 400 |
| `PromoCodeTests` | скидка применена, `min_order_amount`, просрочка промокода |
| `PromoTests` | активные акции на главной, скрытие неактивных, `new_price` по `discount_percent` |
| `AiRecommendTests` | пустой запрос 400, fallback без API-ключей 200 + `source: fallback`, фильтр «без сыра» исключает сырные блюда |
| `AdminApiTests` | промокоды/акции CRUD, защита категорий, бан юзера (себя нельзя), дэшборд по числам, 401/403 для гостей и клиентов |
| `EmailTests` | письмо админу о новом заказе (`on_commit`), без SMTP не отправляется |

Запуск одного класса:
```powershell
.venv\Scripts\python.exe manage.py test api.tests.OrderTests --verbosity=2
```

---

## 🎬 Презентация

* `presentation.html` — слайды (открой в браузере, стрелки `←` `→`, `F` — fullscreen)
* `ui-mockup-main.html` — макет главной (карточки `Promo`, меню, корзина)

Оба файла в корне репо — работают без сервера (`file://`).

---

## 🛠️ Админка

`http://127.0.0.1:8000/admin/` — 8 моделей: `User` (phone), `Category`, `Dish`, `Favorite`, `Order`, `OrderItem`, `PromoCode`, `Promo`.

Полезно: у `Dish` фильтры по `category`/`is_available`, у `Order` — по `status`.

---

## 🖥️ Админ-панель (React)

Своя полноценная панель в папке `admin/` — Vite + React + TypeScript + TanStack Query + React Router.

**Прод-режим без Node на сервере** — сборка раздаёт Django по `/panel/`:

```powershell
cd admin
npm install
npm run build        # соберёт панель в admin/dist
docker compose up -d --build web   # пересборка образа вместе с панелью
# ▶ http://127.0.0.1:8000/panel/
```

**Дев-режим** (быстрая, hot-reload):

```powershell
cd admin
npm run dev   # http://localhost:5173, API ходит на localhost:8000 через CORS
```

| Раздел | Что делает |
|---|---|
| `/orders` | Таблица всех заказов + кнопки смены статуса по матрице переходов |
| `/menu` | Блюда: CRUD с фото и составом; категории: создавать/переименовывать/удалять (с блюдами — нельзя) |
| `/promos` | Акции (с фото) и промокоды: создание, вкл/выкл, удаление |
| `/users` | Список пользователей + бан/разбан (себя забанить нельзя) |
| `/stats` | Заказы и выручка за сегодня, счётчик статусов, топ-5 блюд |

Вход — только для `is_staff`; обычный клиент получит отказ. Логин по номеру телефона и паролю.

E2E-тесты панели (Playwright, нужен поднятый бэкенд на 8000):
```powershell
cd admin
npx playwright test   # 3 теста: полный проход + отдача Django /panel/ + вход через /panel/
```

---

## 📝 Примечания

* **Один ресторан, не агрегатор** — архитектура под одно заведение (нет `Restaurant` модели).
* **Телефон — логин** — `username = phone.replace('+','')` (`api/serializers.py:94`).
* **Цена фиксируется** — `OrderItem.price_at_order` сохраняет цену на момент заказа, не меняется при изменении `Dish.price`.
* **История заказов защищена** — `OrderItem.dish → on_delete=PROTECT`: блюдо с заказами не удалится.
* **Скидка считается на модели** — `Order.calculate_total()` + `Order.apply_promo()`, не в сериализаторе.
* **PostgreSQL по умолчанию** — если в `.env` есть `DATABASE_URL`, Django работает на Postgres; если строки нет — автоматически sqlite3 (локальная разработка).
* **Статика в проде** — Whitenoise отдаёт `/staticfiles/` без nginx; кэш — Redis при `REDIS_URL`, иначе LocMem.
* **Throttling защищает** — `login 5/min`: пароль брутфорсом не подобрать, API от флуда не умрёт.

---

<div align="center">

**Автор:** [Omurbek000](https://github.com/Omurbek000) &nbsp;·&nbsp; 🍣 Онигири &nbsp;·&nbsp; Бишкек &nbsp;·&nbsp; 2026

`MIT` — файл [LICENSE](LICENSE) в корне репозитория

<!-- Сгенерировано с любовью к бишкекской доставке 🍣 -->

</div>
