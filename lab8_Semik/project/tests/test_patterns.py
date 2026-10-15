from datetime import datetime

import pytest

from factories.appointment_factory import AppointmentFactory
from models.entities import Consultation, DiagnosticProcedure, TherapyAppointment
from models.enums import AppointmentStatus
from observers.observers import LoggerObserver, NotificationObserver, StatisticsObserver
from repositories.memory_repository import InMemoryRepository
from services.service import AppointmentService
from strategies.pricing import PreferentialPricing, StandardPricing, UrgentPricing

START = datetime(2026, 10, 20, 9, 0)


@pytest.mark.parametrize("kind, cls", [("therapy", TherapyAppointment),
                                       ("diagnostics", DiagnosticProcedure),
                                       ("consultation", Consultation)])
def test_factory_creates_correct_type(kind, cls):
    assert isinstance(AppointmentFactory.create(kind, 1, "П", "В", START), cls)


def test_factory_unknown_type():
    with pytest.raises(ValueError):
        AppointmentFactory.create("surgery", 1, "П", "В", START)


def test_strategy_changes_price():
    service = AppointmentService(InMemoryRepository(), StandardPricing())
    a = AppointmentFactory.create("therapy", 1, "П", "В", START)
    prices = []
    for strategy in (StandardPricing(), PreferentialPricing(), UrgentPricing()):
        service.set_strategy(strategy)
        prices.append(service.calculate_price(a))
    assert prices == [1500, 750, 3200]


def test_repository_add_get_delete():
    repo = InMemoryRepository()
    a = repo.add(AppointmentFactory.create("consultation", 7, "П", "В", START))
    assert repo.get(7) is a
    repo.delete(7)
    assert repo.get_all() == []
    with pytest.raises(KeyError):
        repo.delete(7)


def test_booking_and_doctor_time_conflict():
    service = AppointmentService(InMemoryRepository(), StandardPricing())
    service.book("therapy", "Иванов", "Смирнова", START)
    with pytest.raises(ValueError):
        service.book("consultation", "Петрова", "Смирнова", START.replace(minute=15))
    assert service.book("consultation", "Петрова", "Смирнова", START.replace(minute=30)).id == 2


def test_observers_receive_events():
    service = AppointmentService(InMemoryRepository(), UrgentPricing())
    logger, notifier, stats = LoggerObserver(), NotificationObserver(), StatisticsObserver()
    for observer in (logger, notifier, stats):
        service.attach(observer)
    a = service.book("diagnostics", "Иванов", "Кузнецов", START)
    service.confirm(a.id)
    service.complete(a.id)
    assert len(logger.records) == 3 and len(notifier.sent) == 3
    assert stats.revenue == 3000 * 1.8 + 500
    assert a.status is AppointmentStatus.COMPLETED
    with pytest.raises(ValueError):
        service.cancel(a.id)
