# Лабораторная работа №7 — SOLID. Вариант 15 «Медицинская клиника»

* `v1_problem/clinic.py` — рабочая версия с намеренными нарушениями (`python clinic.py`).
* `v2_refactored/` — версия после рефакторинга (`python main.py`, тесты: `pytest`).

## Нарушения в версии 1 и их исправление

| № | Проблема (v1) | Принцип | Решение (v2) |
|---|---|---|---|
| 1 | `ClinicManager` хранит данные, ведёт медицинскую логику, шлёт письма, печатает отчёты и вызывает `input()` | SRP | `PatientService`, `AppointmentService`, `ReportService`, репозитории, `ConsoleUI` |
| 2 | `conduct()` выбирает вид приёма через `if/elif` | OCP | абстракция `Procedure` и классы `TherapyProcedure`, `DiagnosticsProcedure`, `ConsultationProcedure`; `VaccinationProcedure` добавлена без изменения сервиса |
| 3 | `Patient.prescribe()` бросает `NotImplementedError` | LSP | метод `prescribe` есть только у `Doctor`; `FileRepository` и `InMemoryRepository` взаимозаменяемы |
| 4 | Огромный интерфейс `ClinicStorageInterface` | ISP | протоколы `Readable` и `Writable`; `ReportService` зависит только от `Readable` |
| 5 | `self.sender = EmailSender()` внутри класса | DIP | `Notifier` (Protocol) передаётся через конструктор; реализации `ConsoleNotifier`, `EmailNotifier`, `SmsNotifier` |
| 6 | Бизнес-логика вызывает `input()`/`print()` | SRP | ввод-вывод только в `ui/console.py` |

## Сравнение

| Характеристика | До | После |
|---|---|---|
| Ответственность классов | один «божественный» класс | отдельные сервисы, репозитории, UI |
| Зависимости | жёстко созданы внутри | внедряются через конструктор |
| Расширяемость | правка `if/elif` | новый класс `Procedure`/`Notifier`/репозитория |
| Тестируемость | мешают `input()` и реальная рассылка | сервисы тестируются с `FakeNotifier` |
| Связность | низкая | высокая |
| Абстракции | нет | `Repository`, `Readable`, `Writable`, `Notifier`, `Procedure` |
