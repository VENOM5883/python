# Лабораторная работа №9 — TCP, клиент-сервер. Вариант 15 «Страхование» (сущность `Policy`)

Запуск (стандартная библиотека Python 3.10+):
```
python server.py            # порт 5015
python client.py            # можно открыть 3 и более клиентов одновременно
python demo_timeout.py      # демонстрация тайм-аута
pytest                      # тесты (нужен pytest)
```

Архитектура: `client.py → TCP → server.py → service.py → repository.py`.
Формат: newline-delimited JSON, запрос `{"request_id", "command", "data"}`,
ответ `{"request_id", "status": "ok", "data"}` или `{"request_id", "status": "error", "error"}`.

| Команда | Запрос (`data`) | Ответ | Назначение |
|---|---|---|---|
| `list` | `{"insurance_type"?}` | список полисов | список |
| `get` | `{"id"}` | полис | получение |
| `create` | `{"holder","insurance_type","insured_value","term_months"}` | полис | создание |
| `update` | `{"id", ...поля}` | полис | изменение |
| `delete` | `{"id"}` | `{"deleted"}` | удаление |
| `calculate_cost` | `{"id","claims"?,"driver_experience"?}` | расчёт | операция варианта: стоимость полиса |
| `ping` | `{}` | `{"message":"pong"}` | проверка связи |

Стоимость = страховая сумма × тариф типа (auto 4.5 %, property 1.2 %, travel 3 %, health 6 %) × срок/12
× (1 + 0.15 × число прошлых страховых случаев) × 1.5 для водителя со стажем < 3 лет.
