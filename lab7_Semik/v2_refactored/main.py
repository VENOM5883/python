"""Лабораторная работа №7. SOLID. Версия 2 (после рефакторинга).
Вариант 15. Медицинская клиника. Сборка зависимостей (Composition Root).
"""
from pathlib import Path

from infrastructure.notifier import ConsoleNotifier, EmailNotifier, SmsNotifier
from models.entities import Appointment, Doctor, Patient
from repositories.file_repository import FileRepository
from repositories.memory_repository import InMemoryRepository
from services.domain_service import AppointmentService, PatientService, ReportService
from ui.console import ConsoleUI

DATA = Path(__file__).with_name("data")


def build(storage: str = "1", channel: str = "1") -> ConsoleUI:
    if storage == "2":
        DATA.mkdir(exist_ok=True)
        patients = FileRepository(DATA / "patients.json", Patient)
        doctors = FileRepository(DATA / "doctors.json", Doctor)
        appointments = FileRepository(DATA / "appointments.json", Appointment)
    else:
        patients, doctors, appointments = InMemoryRepository(), InMemoryRepository(), InMemoryRepository()
    if not doctors.get_all():
        doctors.add(Doctor(1, "Смирнова Елена Викторовна", "терапевт"))
        doctors.add(Doctor(2, "Кузнецов Олег Петрович", "кардиолог"))
    notifier = {"2": EmailNotifier, "3": SmsNotifier}.get(channel, ConsoleNotifier)()
    return ConsoleUI(PatientService(patients, notifier),
                     AppointmentService(appointments, patients, doctors, notifier),
                     ReportService(appointments, patients, doctors))


def main() -> None:
    storage = input("Выберите хранилище:\n1. Память\n2. Файл\n> ").strip()
    channel = input("Канал уведомлений:\n1. Консоль\n2. Email\n3. SMS\n> ").strip()
    build(storage, channel).run()


if __name__ == "__main__":
    main()
