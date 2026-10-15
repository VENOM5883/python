# Лабораторная работа №12 — SQLAlchemy ORM. Вариант 15 «Аптека»

Сущности: `Customer`, `Medicine`, `Purchase` (+ `PurchaseItem` — позиции покупки, связь N:M «покупка — лекарство»).
Транзакционная операция — покупка лекарств: проверка остатка и рецепта, списание остатков, создание покупки
и позиций, расчёт суммы (скидка 5 % по карте); при ошибке — `rollback`.

```
pip install -r requirements.txt
cp .env.example .env          # указать DATABASE_URL для PostgreSQL
python -m app.main            # запуск из папки lab12_Semik
pytest                        # 7 тестов (SQLite в памяти)
```
Без `DATABASE_URL` используется SQLite-файл `pharmacy.db` (для проверки без сервера PostgreSQL).
Для PostgreSQL: `CREATE DATABASE pharmacy;` и `DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/pharmacy`.

| Требование | Реализация |
|---|---|
| CRUD | `add/get/list/update/delete_medicine` |
| Поиск | `search()` — `ilike` по названию и производителю |
| Фильтрация, несколько условий | `filter(category, max_price, in_stock)` через `and_()` |
| Сортировка | `name`, `price`, `-price`, `quantity` |
| Связи | `Customer 1:N Purchase`, `Purchase N:M Medicine` через `PurchaseItem`; `customer_purchases()` |
| Ограничения | PK, FK (`RESTRICT`/`CASCADE`), `UNIQUE(phone)`, `UNIQUE(name, form)`, `CHECK(price > 0)`, NOT NULL |
| Агрегаты | `statistics()` — COUNT, SUM, AVG, MIN, MAX |
| Ошибки | отсутствие объекта, дубликат, нарушение FK, ошибка транзакции, неверный ввод |

Структура: `app/models` (ORM-модели) → `app/repositories` (запросы) → `app/services` (бизнес-логика) → `app/main.py` (консоль).
