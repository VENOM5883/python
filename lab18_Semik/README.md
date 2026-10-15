# Лабораторная работа №18 — pytest и unittest.mock. Вариант 15 «Медицинский центр»

Система записи на приём: регистрация пациента, добавление врача, создание и отмена записи,
запрет двойной записи врача на одно время.

```
pip install -r requirements.txt
python -m src.main                                  # консольный интерфейс
pytest                                              # 40 тестов
pytest --cov=src --cov-report=term-missing          # покрытие (service-слой ~98 %)
```

Архитектура: `src/main.py (интерфейс) → src/services/clinic_service.py → src/repositories/sqlite_repository.py → SQLite`.

| Вид тестов | Где | Количество |
|---|---|---|
| unit (сервис с Mock-репозиторием) | `tests/unit/test_clinic_service.py` | 16 функций (+ параметризация) |
| unit (валидация) | `tests/unit/test_validation.py` | 3 функции |
| Mock / patch | `Mock()` репозитория и SMS-уведомлений, `patch("...now")`, `assert_called_once_with`, `side_effect` | 8+ |
| параметризованные | границы длительности, некорректные ФИО, телефоны, время, id пациента | 5 |
| интеграционные (Service → Repository → SQLite) | `tests/integration/test_repository.py` | 3 |

Проверяемые граничные значения: длительность 9/10/120/121 минут, запись ровно «сейчас», на 31 день вперёд,
07:59 и последний слот 19:30, пустая строка, 101 символ, id = 0 / −1.
