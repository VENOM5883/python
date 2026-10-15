"""Сервис записи на приём: использует Repository, Factory, Strategy и Observer."""
from __future__ import annotations

from datetime import datetime, timedelta

from factories.appointment_factory import AppointmentFactory
from interfaces.repository import Repository
from interfaces.strategies import Observer, PricingStrategy
from models.entities import Appointment
from models.enums import AppointmentStatus


class AppointmentService:
    def __init__(self, repository: Repository, strategy: PricingStrategy) -> None:
        self.repository = repository
        self.strategy = strategy
        self._observers: list[Observer] = []
        self._next_id = 1

    # --- Observer (Subject) ---
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def _notify(self, event: str, appointment: Appointment) -> None:
        for observer in self._observers:
            observer.update(event, appointment)

    # --- Strategy ---
    def set_strategy(self, strategy: PricingStrategy) -> None:
        self.strategy = strategy

    def calculate_price(self, appointment: Appointment) -> float:
        return self.strategy.calculate(appointment)

    # --- бизнес-операции ---
    def book(self, kind: str, patient: str, doctor: str, start: datetime, **extra) -> Appointment:
        appointment = AppointmentFactory.create(kind, self._next_id, patient, doctor, start, **extra)
        end = start + timedelta(minutes=appointment.duration_min)
        for other in self.repository.get_all():
            other_end = other.start + timedelta(minutes=other.duration_min)
            if (other.doctor == doctor and other.status is not AppointmentStatus.CANCELLED
                    and start < other_end and other.start < end):
                raise ValueError(f"У врача {doctor} это время занято")
        appointment.price = self.calculate_price(appointment)
        self._next_id += 1
        self.repository.add(appointment)
        self._notify("запись создана", appointment)
        return appointment

    def _get(self, appointment_id: int) -> Appointment:
        appointment = self.repository.get(appointment_id)
        if appointment is None:
            raise KeyError(f"Запись {appointment_id} не найдена")
        return appointment

    def confirm(self, appointment_id: int) -> Appointment:
        return self._change(appointment_id, AppointmentStatus.CONFIRMED, "запись подтверждена")

    def complete(self, appointment_id: int) -> Appointment:
        return self._change(appointment_id, AppointmentStatus.COMPLETED, "приём завершён")

    def cancel(self, appointment_id: int) -> Appointment:
        return self._change(appointment_id, AppointmentStatus.CANCELLED, "запись отменена")

    def _change(self, appointment_id: int, status: AppointmentStatus, event: str) -> Appointment:
        appointment = self._get(appointment_id)
        if appointment.status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
            raise ValueError(f"Запись уже в статусе «{appointment.status.value}»")
        appointment.status = status
        self.repository.add(appointment)
        self._notify(event, appointment)
        return appointment
