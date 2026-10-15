# Лабораторная работа №20 — Контейнеризация и CI/CD. Вариант 15 «Аптека»

Задание варианта: контейнеризировать приложение и БД, добавить автоматическую сборку образа.
Приложение — REST API аптеки (FastAPI + SQLAlchemy): каталог препаратов и продажа с контролем остатка.

## Технологии
Python 3.12, FastAPI, SQLAlchemy, PostgreSQL 16, Docker (multi-stage), Docker Compose, pytest + pytest-cov, ruff,
GitHub Actions.

## Архитектура
```
docker compose ─┬─ app (pharmacy-api, порт 8000, /health, healthcheck) ──► db
                └─ db  (postgres:16, volume postgres_data, pg_isready)
```

## Переменные окружения (`.env`, в Git не попадает; шаблон — `.env.example`)
`DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, LOG_LEVEL, APP_VERSION`
(или одной строкой `DATABASE_URL`). Без них приложение использует SQLite — удобно для локальной проверки.

## Запуск
```
git clone https://github.com/VENOM5883/python && cd python/lab20_Semik
cp .env.example .env          # задать DATABASE_PASSWORD
docker compose up --build     # сборка и запуск
docker compose ps             # состояние (healthy)
docker compose logs -f app    # логи
curl localhost:8000/health    # {"status": "healthy", "database": true, ...}
docker compose down && docker compose up   # данные БД сохраняются в volume postgres_data
```
Без Docker: `pip install -r requirements-dev.txt && uvicorn src.main:app`.

## Тесты и качество
```
ruff check .
pytest            # unit (Mock) + integration (SQLite), порог покрытия 80 % (--cov-fail-under)
docker build -t pharmacy-api .
```

## API
`GET /health`, `GET/POST /medicines`, `GET/PUT/DELETE /medicines/{id}`, `POST /sales`.

## CI/CD
Workflow `.github/workflows/lab20-ci.yml` (в корне репозитория) запускается при push и pull request,
если изменились файлы `lab20_Semik/`:
`Checkout → Python setup → Install → Lint (ruff) → Pytest + coverage → Docker build → smoke-тест /health`.
Этап `docker` выполняется только после успешного `test`; при падении тестов pipeline завершается ошибкой.
