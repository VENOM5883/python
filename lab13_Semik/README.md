# Лабораторная работа №13 — MongoDB и Redis. Вариант 15 «Медицинская клиника — приёмы»

```
pip install -r requirements.txt
docker compose up -d                       # MongoDB и Redis (при наличии Docker)
export MONGO_URL=mongodb://localhost:27017 REDIS_URL=redis://localhost:6379/0
python -m app.main                         # из папки lab13_Semik
pytest                                     # 13 тестов
```
Если `MONGO_URL`/`REDIS_URL` не заданы или серверы недоступны, приложение работает на `mongomock` и
`fakeredis` (имитация в памяти) — этого достаточно для проверки логики и скриншотов.

## MongoDB: база `clinic`, коллекция `appointments` (24 документа)
```json
{"patient": {"full_name": "Иванов Иван Иванович", "birth_year": 1985, "phone": "+79001000000"},
 "doctor": {"id": 1, "full_name": "Смирнова Елена Викторовна", "specialty": "терапевт", "cabinet": 101},
 "specialty": "терапевт", "date": "2026-10-20", "time": "09:00", "status": "completed",
 "diagnosis": "ОРВИ", "prescriptions": ["Парацетамол", "Обильное питьё"]}
```
Запросы (`app/repository.py`): фильтры по статусу, специальности+дате, периоду; сортировки по дате/времени
(прямая и обратная); `limit` (ближайшие приёмы); вложенное поле `patient.full_name`; элемент массива
`prescriptions`; агрегации `count_by_status`, `doctors_workload`, `top_prescriptions` (`$unwind`).
Индексы: `doctor_date_time` (расписание врача), `status_specialty` (выборки по статусу/специальности).

## Redis
| Ключ | Тип | Назначение | TTL |
|---|---|---|---|
| `appointment:{id}` | String (JSON) | кэш приёма (Cache-Aside) | 120 с |
| `doctor:{id}` | Hash | кэш информации о враче | 600 с |
| `schedule:{doctor}:{date}` | List | расписание врача | 300 с |
| `upcoming` | Sorted Set | ближайшие приёмы (score = дата-время) | — |
| `recent_queries` | List | последние поисковые запросы | — |

Операции: GET, SET (ex), DELETE, EXPIRE, TTL, HSET, HGETALL, RPUSH, LRANGE, LPUSH, LTRIM, ZADD, ZREM, ZRANGE,
EXISTS, KEYS, FLUSHDB. При изменении/удалении приёма кэш `appointment:{id}` и `schedule:...` удаляется.
Пункт меню 10 — сравнение времени MongoDB и Redis на 100/1 000/10 000 запросов.
