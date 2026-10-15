# Лабораторная работа №15 — Flask. Вариант 15 «Аптека»

Сущности: `Medicine`, `Category`, `Purchase` (+ `PurchaseItem`). Каталог лекарственных средств и оформление покупки.

```
pip install -r requirements.txt
cp .env.example .env      # DATABASE_URL для PostgreSQL; без него — SQLite pharmacy_web.db
python run.py             # http://127.0.0.1:5000
pytest                    # 6 тестов (страницы, формы, поиск/фильтры/сортировка, покупка, REST API)
```

## Страницы (Jinja2, наследование от base.html)
| URL | Страница |
|---|---|
| `/` | главная: количество препаратов, категорий, покупок |
| `/medicines?search=&category=&prescription=&in_stock=on&sort=` | каталог: поиск, 2+ фильтра, 4 сортировки |
| `/medicines/<id>` | карточка препарата (связь с категорией и продажами) |
| `/medicines/create`, `/medicines/<id>/edit` | формы создания и редактирования |
| `/medicines/<id>/delete` (POST) | удаление с подтверждением |
| `/categories/<id>` | препараты категории |
| `/purchases` | оформление покупки (транзакция) и история |
| 404 | собственный шаблон `404.html` |

## REST API (JSON)
`GET/POST /api/medicines`, `GET/PUT/PATCH/DELETE /api/medicines/<id>`, `POST /api/purchases`.
Коды: 200, 201, 204, 400, 404, 409.

Архитектура: Application Factory (`app/__init__.py`), Blueprint `web` и `api` → `services` → `repositories` →
SQLAlchemy → PostgreSQL/SQLite. Настройки — переменные окружения (`DATABASE_URL`, `SECRET_KEY`, `FLASK_ENV`).
Логируются запуск, все HTTP-запросы и изменения данных.
