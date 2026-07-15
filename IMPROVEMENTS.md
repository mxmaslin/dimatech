# Рекомендации по развитию (не реализовано)

## CI/CD

- GitHub Actions workflow добавлен (lint + pytest + docker build).
- Опционально: integration job с PostgreSQL service (сейчас unit/e2e на SQLite in-memory).

## DDD

- **Unit of Work** pattern для транзакций across repositories.
- Domain events для `UserRegistered`, `WebhookDelivered`.

## Observability

- Request ID middleware.
- Prometheus `/metrics` endpoint.

## Безопасность

- JWT secret rotation; refresh token blacklist in Redis.
- Rate limiting на `/auth/login`.

## Исправлено в этом review

- `.github/workflows/ci.yml` — ruff + pytest + docker build на push/PR.
