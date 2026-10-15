# Лабораторная работа №11 — Реляционные и нереляционные БД, кэш, CDN
Вариант 15: «Медицинская клиника», основная сущность `Appointment`, кэшируется расписание врачей,
через CDN раздаются фотографии врачей и отделений.

```
pip install -r requirements.txt
python app.py          # REST API + SQLite (clinic.db создаётся автоматически из sql/schema.sql и sql/seed.sql)
python nosql_demo.py   # операции Redis (SET/GET/EXPIRE/INCR/DELETE), cache-aside, документная модель
python cdn_server.py   # имитация CDN: origin :8001 и edge :8002
python cdn_check.py    # исследование заголовков, времени, HIT/MISS, ETag/304
pytest                 # 14 тестов
```
Если задан `REDIS_URL` и сервер Redis доступен, используется настоящий Redis, иначе — `fakeredis` (имитация).

## База данных (SQLite)
`departments 1:N doctors 1:N appointments N:1 patients`; связь N:M `appointments — services`
через `appointment_services`. Ограничения: PRIMARY KEY, FOREIGN KEY, NOT NULL, UNIQUE, CHECK.
Индексы: `idx_appointments_doctor_date` (расписание врача на дату), `idx_appointments_status`
(свободные записи), `idx_doctors_specialty`. 16 SQL-запросов — `sql/queries.sql`.

Транзакция: `POST /appointments/{id}/complete` — смена статуса и добавление оказанных услуг
выполняются атомарно (`with connection:` → COMMIT/ROLLBACK). Все запросы параметризованы (`?`).

## API
| Метод | URL | Назначение |
|---|---|---|
| GET | /appointments?doctor_id&specialty&status&date&sort&order | список |
| GET/PUT/PATCH/DELETE | /appointments/{id} | CRUD |
| POST | /appointments | создание (201) |
| GET | /appointments/free | свободные записи |
| POST | /appointments/{id}/complete | транзакция |
| GET | /doctors/{id}/schedule?date= | расписание врача через Redis (cache-aside, TTL 60 с) |

## Где хранятся данные
| Данные | Хранилище | Почему |
|---|---|---|
| Записи, пациенты, врачи, услуги | SQLite/PostgreSQL | связи, транзакции, целостность |
| Расписание врача на день | Redis (TTL 60 с) | часто читается, быстро устаревает, легко пересчитать |
| Фото врачей, CSS, JS | CDN | статичные публичные файлы, кэшируются близко к пользователю |

| Характеристика | PostgreSQL | MongoDB | Redis | CDN |
|---|---|---|---|---|
| Назначение | основной источник данных | гибкие документы | кэш, счётчики | раздача статики |
| Структура | таблицы, схема | JSON-документы | ключ–значение | файлы |
| Транзакции | ACID | на уровне документа/сессии | ограничены | нет |
| Когда использовать | связанные данные | меняющаяся структура | быстрый доступ к временным данным | изображения, CSS, JS |
