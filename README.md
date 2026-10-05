[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)

# payproc


## Запуск

Все файлы сборки в `deploy/`.

### 1. prod-версия (gunicorn)


```bash
docker compose -f deploy/docker-compose.prod.yml up --build
```

### 2. dev-версия


```bash
docker compose -f deploy/docker-compose.dev.yml up --build
```


### URLs:
- **API**: [http://localhost:8000](http://localhost:8000)
- **API документация**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Запуск вне Docker

```bash
uv sync
uv pip install -e .
cp .env.example .env
uv run alembic upgrade head

uv run python src/main.py
uv run faststream run server.consumer.worker:app
```

---

## Примеры

Default static API-ключ: `secret-static-api-key`.

### 1. Создание платежа (POST /api/v1/payments)

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-static-api-key" \
  -H "Idempotency-Key: test-order-uuid-001" \
  -d '{
    "amount": "300",
    "currency": "RUB",
    "description": "Булка",
    "metadata": {
      "user_id": 42,
      "order_number": "ORD-2026-789"
    },
    "webhook_url": "https://httpbin.org/post"
  }'
```

**Ответ (202 Accepted):**
```json
{
  "payment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "created_at": "2026-10-05T14:30:00.123456Z"
}
```

### 2. Проверка идемпотентности
При повторной отправке запроса с тем же `Idempotency-Key: test-order-uuid-001` сервер возвращает существующий платеж без создания дубликата и без повторной публикации в очередь.

### 3. Получение информации о платеже (GET /api/v1/payments/{payment_id})

```bash
curl -X GET "http://localhost:8000/api/v1/payments/3fa85f64-5717-4562-b3fc-2c963f66afa6" \
  -H "X-API-Key: secret-static-api-key"
```

**Ответ (200 OK):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "amount": 300,
  "currency": "RUB",
  "description": "Булка",
  "metadata": {
    "user_id": 42,
    "order_number": "ORD-2026-789"
  },
  "status": "succeeded",
  "idempotency_key": "test-order-uuid-001",
  "webhook_url": "https://httpbin.org/post",
  "created_at": "2026-10-05T14:30:00.123456Z",
  "processed_at": "2026-10-05T14:30:03.456789Z"
}
```

### 4. Формат Webhook-уведомления

После завершения обработки внешним шлюзом consumer отправляет POST-запрос на указанный клиентом `webhook_url`:

```json
{
  "event": "payment.processed",
  "payment_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "succeeded",
  "amount": 300,
  "currency": "RUB",
  "description": "Булка",
  "metadata": {
    "user_id": 42,
    "order_number": "ORD-2026-789"
  },
  "processed_at": "2026-10-05T14:30:03.456789Z"
}
```

---

## Lint (WPS)


```bash
uv run flake8 .
uv run ruff check
uv run mypy .

# or
pre-commit run --all-files
```
