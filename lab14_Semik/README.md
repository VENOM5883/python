# Clinic Appointments API — лабораторная работа №14 (FastAPI), вариант 15

REST API записей на приём в медицинскую клинику: CRUD, поиск, фильтрация, сортировка, пагинация,
статистика, кэширование `GET /appointments/{id}` в Redis.

**Технологии:** FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL (или SQLite локально), Redis (или fakeredis), pytest.

## Запуск
```
pip install -r requirements.txt
uvicorn app.main:app --reload            # без .env: SQLite ./clinic.db + fakeredis
```
Docker: `cp .env.example .env && docker compose up --build`.
Swagger: http://127.0.0.1:8000/docs, ReDoc: http://127.0.0.1:8000/redoc.

## Переменные окружения
`DATABASE_URL`, `REDIS_URL`, `APP_ENV`, `CACHE_TTL` — см. `.env.example`.

## API
| Метод | URL | Назначение | Код |
|---|---|---|---|
| GET | /appointments?specialty&doctor&status&date&sort&order&skip&limit | список | 200 |
| GET | /appointments/{id} | запись (заголовок `X-Cache: HIT/MISS`) | 200/404 |
| POST | /appointments | создание | 201/409/422 |
| PUT | /appointments/{id} | полное изменение | 200/404 |
| PATCH | /appointments/{id} | частичное изменение | 200/400/404 |
| DELETE | /appointments/{id} | удаление | 204/404 |
| GET | /appointments/search?q= | поиск по пациенту/врачу/специальности | 200 |
| GET | /appointments/statistics | статистика (async endpoint) | 200 |
| GET | /health | проверка состояния | 200 |

Пример: `curl -X POST localhost:8000/appointments -H "Content-Type: application/json" -d
'{"patient":"Тестов Тест","doctor":"Белова М.И.","specialty":"окулист","date":"2026-10-25","time":"10:00","cabinet":120}'`

Архитектура: `Router (routers/) → Service (services/) → Repository (repositories/) → SQLAlchemy → БД`,
`Service ↔ Redis (cache.py)`; зависимости внедряются через `Depends`.

## Тесты
`pytest` — 17 тестов (CRUD, 404/409/422, фильтр, сортировка, пагинация, поиск, статистика, cache hit/miss/invalidation).
