# DimaTech — REST API Test Assignment

Async REST API built with **Sanic**, **SQLAlchemy 2.0** (async), **PostgreSQL** in Clean Architecture.

## Stack

- **Framework:** Sanic (async)
- **ORM:** SQLAlchemy 2.0 (async)
- **Database:** PostgreSQL 16
- **Migrations:** Alembic
- **Auth:** JWT (HS256) + bcrypt
- **Validation:** Pydantic v2
- **Tests:** pytest + pytest-asyncio

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
# Copy environment config
cp .env.example .env

# Build and start services
make docker-up
# or: docker compose up --build -d

# Check logs
make docker-logs
```

The API will be available at `http://localhost:8000`.

### Option 2: Local development

Prerequisites: Python 3.12+, PostgreSQL 16+

```bash
# 1. Create PostgreSQL database
createdb dimatech

# 2. Copy environment config
cp .env.example .env
# Edit .env if needed (DATABASE_URL, secrets)

# 3. Install dependencies
make install

# 4. Run migrations
alembic upgrade head

# 5. Start development server
make run
```

The API will be available at `http://localhost:8000`.

## Default Credentials

| Role  | Email                | Password  |
|-------|----------------------|-----------|
| User  | user@example.com     | user123   |
| Admin | admin@example.com    | admin123  |

## API Endpoints

### Authentication

| Method | Endpoint       | Auth  | Description          |
|--------|----------------|-------|----------------------|
| POST   | /auth/login    | —     | Login by email/password |
| GET    | /auth/admins/me | admin | Get admin profile    |

### User endpoints

| Method | Endpoint               | Auth | Description              |
|--------|------------------------|------|--------------------------|
| GET    | /users/me              | user | Get own profile          |
| GET    | /users/me/accounts     | user | List own accounts        |
| GET    | /users/me/payments     | user | List own payments        |

### Admin endpoints

| Method | Endpoint                   | Auth  | Description              |
|--------|----------------------------|-------|--------------------------|
| POST   | /users/                    | admin | Create a user            |
| GET    | /users/                    | admin | List all users           |
| PUT    | /users/:user_id            | admin | Update a user            |
| DELETE | /users/:user_id            | admin | Delete a user            |
| GET    | /users/:user_id/accounts   | admin | Get user accounts        |

### Payment webhook

| Method | Endpoint           | Auth | Description                  |
|--------|--------------------|------|------------------------------|
| POST   | /payments/webhook  | —    | Process payment webhook      |

### Health

| Method | Endpoint   | Description          |
|--------|------------|----------------------|
| GET    | /health    | Health check         |

## Payment Webhook

```json
{
  "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
  "user_id": 1,
  "account_id": 1,
  "amount": 100.00,
  "signature": "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
}
```

The signature is SHA256 of concatenated values in alphabetical key order plus the secret key:
`{account_id}{amount}{transaction_id}{user_id}{secret_key}`

## Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest -v --cov=src --cov-report=term-missing --cov-report=html
```

## Project Structure

```
src/
├── domain/            # Business entities (no framework dependencies)
│   ├── entities.py
│   ├── value_objects.py
│   └── interfaces.py
├── application/       # Use cases & DTOs
│   ├── dto.py
│   ├── errors.py
│   └── use_cases/
├── infrastructure/    # Database, auth, config
│   ├── config.py
│   ├── database/
│   └── auth/
├── presentation/      # Sanic routes, middleware, error handlers
│   ├── routes/
│   ├── middleware.py
│   └── errors.py
├── container.py       # DI container
└── main.py            # App factory
```

## Available Make Commands

```bash
make install     # Install dependencies
make run         # Run dev server
make test        # Run tests with coverage
make lint        # Check code quality
make format      # Format code
make docker-up   # Start Docker services
make docker-down # Stop Docker services
make clean       # Clean temporary files
```
