"""Лабораторная работа №8. Паттерны проектирования.
Вариант 15. Медицинская клиника — система записи на приём.
Паттерны: Repository, Factory, Strategy, Observer.
"""
from observers.observers import LoggerObserver, NotificationObserver, StatisticsObserver
from repositories.memory_repository import InMemoryRepository
from services.service import AppointmentService
from strategies.pricing import StandardPricing
from ui.console import ConsoleUI


def main() -> None:
    service = AppointmentService(InMemoryRepository(), StandardPricing())
    statistics = StatisticsObserver()
    for observer in (LoggerObserver(), NotificationObserver(), statistics):
        service.attach(observer)
    ConsoleUI(service, statistics).run()


if __name__ == "__main__":
    main()
