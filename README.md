# DimaTech — REST API финтех-сервиса

## О проекте

Асинхронный бэкенд учебного финтех-приложения: пользователи с личными счетами, администраторы управляют аккаунтами, внешний платёжный провайдер шлёт подписанные webhook'и о пополнении. Реализовано как **тестовое задание** с акцентом на Clean Architecture, безопасность webhook'ов и production-паттерны (health, rate limit, CORS).

## Какую задачу решает

Моделирует типичный **B2C fintech backend**:

- **JWT-аутентификация** — роли `user` / `admin`, разделение эндпоинтов;
- **Личный кабинет** — профиль, список счетов и история платежей пользователя;
- **Админка** — CRUD пользователей, просмотр счетов;
- **Webhook платежей** — HMAC-подобная SHA256-подпись, идемпотентность по `transaction_id`, атомарное зачисление на баланс;
- **Защита webhook'а** — rate limit 10 req/min на IP, верификация подписи до записи в БД.

Use case'ы не зависят от Sanic/SQLAlchemy — domain и application тестируются отдельно от HTTP-слоя.

## Как устроено

```
HTTP (Sanic routes + middleware)
    → DI Container
    → Application use cases (auth, users, payments/webhook)
    → Domain entities + ports (UnitOfWork, SecretKeyProvider)
    → Infrastructure (SQLAlchemy async repos, JWT, bcrypt, config)
```

Слои: `domain/` (сущности без фреймворков) → `application/` (DTO, use cases) → `infrastructure/` (БД, auth) → `presentation/` (роуты, CORS, rate limiter, error handlers). Webhook: `ProcessPaymentWebhookUseCase` проверяет подпись, создаёт платёж идемпотентно и увеличивает баланс счёта в одной транзакции.

## Стек и почему

| Технология | Зачем |
|------------|-------|
| **Sanic** | Нативный async HTTP — подходит под I/O-bound webhook'и и параллельные запросы к PostgreSQL |
| **SQLAlchemy 2.0 async** | Единый стиль с production Django/FastAPI-проектами; явные репозитории за портами UoW |
| **PostgreSQL 16** | Транзакции для webhook + баланс; миграции Alembic |
| **JWT (HS256) + bcrypt** | Stateless auth для API; пароли не в открытом виде |
| **Pydantic v2** | Валидация DTO на границе application/presentation |
| **pytest-asyncio** | Async integration-тесты use case'ов и HTTP-слоя |

## Быстрый старт

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Скопировать конфиг окружения
cp .env.example .env

# Собрать и запустить сервисы
make docker-up
# или: docker compose up --build -d

# Посмотреть логи
make docker-logs

# Наполнить БД тестовыми данными
docker compose exec app python scripts/seed.py
```

API будет доступно по адресу `http://localhost:8001`.

### Вариант 2: Локальная разработка

Требования: Python 3.11+, PostgreSQL 16+

```bash
# 1. Создать базу данных PostgreSQL
createdb dimatech

# 2. Скопировать конфиг окружения
cp .env.example .env
# При необходимости отредактировать .env (DATABASE_URL, секреты)

# 3. Установить зависимости (автоматически создаёт .venv)
make install

# 4. Активировать виртуальное окружение
source .venv/bin/activate

# 5. Применить миграции
alembic upgrade head

# 6. Наполнить БД тестовыми данными (первый запуск)
python scripts/seed.py

# 7. Запустить dev-сервер
make run
# или: sanic src.main:create_app --factory --host=0.0.0.0 --port=8000 --dev
```

> Все `make`-команды (`make test`, `make lint` и т.д.) автоматически создают и используют виртуальное окружение `.venv`. Если хотите запускать команды напрямую — сначала активируйте venv: `source .venv/bin/activate`.

API будет доступно по адресу `http://localhost:8000`.

## Учётные данные по умолчанию

После запуска `python scripts/seed.py` будут созданы тестовые аккаунты:

| Роль  | Email                | Пароль   |
|-------|----------------------|----------|
| User  | user@example.com     | user123  |
| Admin | admin@example.com    | admin123 |

## API Endpoints

### Аутентификация

| Метод | Endpoint        | Доступ | Описание                    |
|-------|-----------------|--------|-----------------------------|
| POST  | /auth/login     | —      | Вход по email/password      |
| GET   | /auth/admins/me | admin  | Профиль администратора      |

### Пользовательские endpoints

| Метод | Endpoint              | Доступ | Описание                 |
|-------|-----------------------|--------|--------------------------|
| GET   | /users/me             | user   | Свой профиль             |
| GET   | /users/me/accounts    | user   | Список своих счетов      |
| GET   | /users/me/payments    | user   | Список своих платежей    |

### Администраторские endpoints

| Метод | Endpoint                  | Доступ | Описание                  |
|-------|---------------------------|--------|---------------------------|
| POST  | /users/                   | admin  | Создать пользователя      |
| GET   | /users/                   | admin  | Список пользователей      |
| PUT   | /users/:user_id           | admin  | Обновить пользователя     |
| DELETE| /users/:user_id           | admin  | Удалить пользователя      |
| GET   | /users/:user_id/accounts  | admin  | Счета пользователя        |

### Вебхук платежей

| Метод | Endpoint          | Доступ | Описание                      |
|-------|-------------------|--------|-------------------------------|
| POST  | /payments/webhook | —      | Обработка вебхука платежа     |

### Health check

| Метод | Endpoint       | Описание                                              |
|-------|----------------|-------------------------------------------------------|
| GET   | /health        | Общий статус приложения + проверка подключения к БД   |
| GET   | /health/live   | Liveness-проверка (K8s) — всегда ok                   |
| GET   | /health/ready  | Readiness-проверка (K8s) — проверяет готовность БД    |

### Rate Limiting

| Endpoint          | Лимит                  |
|-------------------|------------------------|
| POST /payments/webhook | 10 запросов / 60 сек на IP |

При превышении возвращается `HTTP 429`:

```json
{"error": "application_error", "detail": "Rate limit exceeded. Try again later."}
```

### CORS

Разрешены все origins, методы `GET/POST/PUT/DELETE/OPTIONS`, заголовки `Content-Type/Authorization`.

## Вебхук платежей

## Вебхук платежей

Тело запроса:

```json
{
  "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
  "user_id": 1,
  "account_id": 1,
  "amount": 100.00,
  "signature": "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
}
```

Подпись — SHA256 от конкатенации полей в алфавитном порядке ключей + секретный ключ:
`{account_id}{amount}{transaction_id}{user_id}{secret_key}`

## Запуск тестов

```bash
# Запустить все тесты
make test

# Запустить с отчётом о покрытии
pytest -v --cov=src --cov-report=term-missing --cov-report=html
```

## Структура проекта

```
├── alembic.ini            # Конфиг Alembic (учитывает $DATABASE_URL)
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── requirements.txt
├── migrations/
│   ├── env.py
│   └── versions/
├── scripts/
│   └── seed.py               # Наполнение БД тестовыми данными
├── src/
    ├── domain/            # Бизнес-сущности (без зависимостей от фреймворков)
    │   ├── entities.py
    │   ├── value_objects.py
    │   └── interfaces.py
    ├── application/       # Use cases и DTO
    │   ├── dto.py
    │   ├── errors.py
    │   └── use_cases/
    ├── infrastructure/    # База данных, аутентификация, конфиг
    │   ├── config.py
    │   ├── database/
    │   └── auth/
    ├── presentation/      # Роуты Sanic, middleware, обработчики ошибок
    │   ├── routes/
    │   ├── middleware.py
    │   ├── cors.py            # CORS middleware
    │   ├── rate_limiter.py    # In-memory rate limiter
    │   ├── errors.py
    │   └── utils.py
    ├── container.py       # DI-контейнер
    └── main.py            # Фабрика приложения
```

## Доступные Make-команды

```bash
make install     # Установить зависимости
make run         # Запустить dev-сервер
make seed        # Наполнить БД тестовыми данными (user/admin)
make test        # Запустить тесты с покрытием
make lint        # Проверить качество кода
make format      # Отформатировать код
make docker-up   # Запустить Docker-сервисы
make docker-down # Остановить Docker-сервисы
make clean       # Очистить временные файлы
```
