# Pharmacy API — итоговый проект (лабораторная работа №21), вариант 15 «Аптека»

Небольшая, но законченная система аптечной сети: каталог препаратов, покупатели, заказы, несколько складов
и **контроль остатков**. Уровень сложности — **A (монолит)**.

## Функциональность
* регистрация и вход (JWT), роли **USER** и **ADMIN**;
* каталог: поиск, фильтр по категории и цене, сортировка, пагинация, доступный остаток по всем складам;
* ADMIN: CRUD препаратов, склады, установка остатков, статистика продаж;
* заказы: оформление, история, смена статуса, отмена с возвратом товара на склады.

### Бизнес-правила (сервисный слой `app/services/services.py`, покрыты тестами)
1. Нельзя заказать больше, чем есть на всех складах; товар списывается со складов по приоритету.
2. Рецептурный препарат отпускается только при наличии рецепта.
3. Статусы: `created → paid → completed`, отмена из `created/paid` возвращает товар на те же склады; завершает заказ только ADMIN.
4. Скидка 5 % постоянному клиенту (сумма завершённых заказов ≥ 5000 руб.).
5. Нельзя удалить препарат, который уже заказывали.
6. Пользователь видит только свои заказы.

## Архитектура
```
Client → FastAPI (app/api/routes.py) → Service (app/services) → Repository (app/repositories)
       → SQLAlchemy → PostgreSQL
```
БД: `users 1:1 customers 1:N orders 1:N order_items N:1 products 1:N stock N:1 warehouses`
(`stock` — связь N:M «товар — склад» с количеством). PK, FK, UNIQUE, CHECK, индексы по `name`, `category`, `customer_id`.

## Стек
Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL 16, PyJWT, pytest/pytest-cov, ruff,
Docker, Docker Compose, GitHub Actions.

## Запуск
```
git clone https://github.com/VENOM5883/python && cd python/lab21_Semik
cp .env.example .env              # заполнить пароли и JWT_SECRET
docker compose up --build         # http://localhost:8000/swagger
```
Без Docker: `pip install -r requirements-dev.txt && uvicorn app.main:app` (SQLite `pharmacy.db`).
Администратор создаётся при первом запуске из `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

## Переменные окружения
`DATABASE_URL, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, JWT_SECRET, JWT_TTL_MINUTES, ADMIN_EMAIL, ADMIN_PASSWORD, LOG_LEVEL`.

## API (документация — `/swagger`, `/redoc`)
| Метод | URL | Доступ | Назначение |
|---|---|---|---|
| POST | /auth/register | все | регистрация (201, 409, 422) |
| POST | /auth/login | все | JWT-токен (200, 401) |
| GET | /auth/profile | USER | профиль |
| GET | /products?q&category&max_price&sort&order&skip&limit | все | каталог |
| GET | /products/{id} | все | препарат (404) |
| POST/PUT/PATCH/DELETE | /products[/{id}] | ADMIN | управление каталогом (201/204/403/409) |
| GET/POST | /warehouses | ADMIN | склады |
| PUT | /warehouses/stock | ADMIN | остаток товара на складе |
| POST | /orders | USER | оформить заказ (201, 409 OUT_OF_STOCK / PRESCRIPTION_REQUIRED) |
| GET | /orders, /orders/{id} | USER/ADMIN | заказы (403 для чужих) |
| PATCH | /orders/{id}/status | USER/ADMIN | paid / completed / cancelled |
| GET | /orders/statistics | ADMIN | статистика |
| GET | /health | все | состояние |

Ошибки возвращаются в едином формате: `{"error": "PRODUCT_NOT_FOUND", "message": "Product with id 15 not found"}`.

## Тесты
`pytest` — 32 теста (+ параметризация): unit (Mock-репозитории, валидация, JWT), интеграционные тесты API (SQLite),
покрытие ~97 % (порог 70 %). `ruff check .` — статический анализ.

## CI
`.github/workflows/lab21-ci.yml`: Install → Lint → Tests + Coverage → Docker Build → smoke-тест `/health`.

## Ограничения
Оплата и уведомления не реализованы (статус `paid` выставляется вручную); асинхронные события и Redis не используются (уровень A).
