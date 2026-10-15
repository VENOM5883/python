# Лабораторная работа №6 — вариант 15 «Медицинская клиника»

Запуск: `python main.py` (Python 3.10+, только стандартная библиотека).

| Файл | Содержимое |
|---|---|
| `models.py` | dataclass `Entity → Person → Patient/Doctor`, `Appointment`, Enum `AppointmentStatus` |
| `decorators.py` | `@log_call`, `@timer`, `@require_status(...)`, `@retry(n)` (все с `@wraps`) |
| `context.py` | `OperationLogger` (`__enter__/__exit__`, пишет `operations.log`), `transaction` (`@contextmanager`, откат) |
| `protocols.py` | Protocol `Reportable` и функция `print_report` |
| `introspection.py` | `type`, `isinstance`, `issubclass`, `hasattr/getattr`, `dir`, `inspect.getmembers/signature` |
| `services.py` | `ClinicService`: CRUD, смена статуса, приёмы врача, средняя длительность, статистика |
| `exceptions.py` | `EntityNotFoundError`, `InvalidStatusTransitionError`, `ValidationError` |
