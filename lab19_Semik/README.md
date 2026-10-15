# Лабораторная работа №19 — Микросервисная архитектура. Вариант 15 «Аптека»

При оформлении заказа товар резервируется на складе.

```
Client → API Gateway :8000
           ├── product-service      (каталог препаратов)      → product-db
           ├── warehouse-service    (остатки и резервы)       → warehouse-db
           ├── order-service        (заказы)                  → order-db
           │      ├─ HTTP → product-service (цены, рецепт)          ┐ Retry +
           │      └─ HTTP → warehouse-service (резерв / снятие)      ┘ Circuit Breaker
           │      └─ событие OrderCreated/OrderCancelled → broker (RabbitMQ)
           └── notification-service (потребитель событий)     → notification-db
```

## Запуск
* Docker: `cp .env.example .env && docker compose up --build` (PostgreSQL ×4, RabbitMQ, 5 сервисов).
  Отказ склада: `docker compose stop warehouse-service`.
* Без Docker (имитация): `pip install -r requirements.txt`, затем `python run_local.py` — все сервисы на SQLite,
  брокер — файловая очередь `.local/events`.
* Сценарий демонстрации: `python demo.py` — заказ, резерв, событие, остановка склада, Retry, Circuit Breaker
  (CLOSED → OPEN → HALF_OPEN → CLOSED).
* Тесты: `./run_tests.sh` — 37 тестов (5 общих + product 9 + warehouse 8 + order 9 + notification 3 + gateway 3).

## Паттерны
| Паттерн | Реализация |
|---|---|
| API Gateway | `gateway/app/main.py`: маршрутизация `/api/{products,stock,reservations,orders,notifications}`, агрегированный `/health` |
| Database per Service | у каждого сервиса своя БД; order-service хранит копию названия/цены, а не FK на чужую таблицу |
| Retry | `common/resilience.py::retry` — 3 попытки, тайм-аут 2 с, задержка 0.2 → 0.4 с (exponential backoff); только сетевые ошибки и 502/504 |
| Circuit Breaker | `CircuitBreaker`: 3 ошибки → OPEN, через 10 с HALF_OPEN, успех → CLOSED |
| Event-Driven | `OrderCreated`, `OrderCancelled`, `OrderCompleted`, `ProductReserved`, `StockReceived` через RabbitMQ (fanout) |
| Компенсация | при ошибке сохранения заказа или отмене заказа снимается резерв на складе |

Каждый сервис: REST API (GET/POST/PUT/DELETE), `GET /health`, журнал
`timestamp service request_id метод endpoint status duration`.
