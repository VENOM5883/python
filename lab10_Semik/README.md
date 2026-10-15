# Лабораторная работа №10 — HTTP и REST API (Flask). Вариант 15 «Медицинская клиника»

```
pip install -r requirements.txt
python app.py        # сервер http://127.0.0.1:5000
python client.py     # консольный HTTP-клиент (requests)
pytest               # 16 тестов
```

Архитектура: `client.py → HTTP → routes.py (Flask) → service.py → repository.py (память)`.

Ресурс `Appointment`: `id, doctor, specialty, date, time, cabinet, patient, status (free/booked/completed/cancelled)`.

| Метод | Endpoint | Назначение | Код |
|---|---|---|---|
| GET | /appointments | список (фильтры `doctor`, `specialty`, `status`, `date`; `sort=datetime\|doctor\|cabinet\|id`, `order=asc\|desc`) | 200 |
| GET | /appointments/{id} | одна запись | 200 / 404 / 400 |
| POST | /appointments | создание | 201 / 400 / 409 |
| PUT | /appointments/{id} | полная замена | 200 |
| PATCH | /appointments/{id} | частичное изменение (например, запись пациента) | 200 |
| DELETE | /appointments/{id} | удаление | 204 / 404 |
| GET | /appointments/free | **свободные записи** (`specialty`, `date`) | 200 |

Пример: `POST /appointments` с телом
`{"doctor":"Белова М.И.","specialty":"окулист","date":"2026-10-22","time":"14:00","cabinet":120}`
→ `201 Created`. Ошибка — `{"error": "...", "code": "VALIDATION_ERROR"}`.
