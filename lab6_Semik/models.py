"""Модели предметной области: медицинская клиника."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AppointmentStatus(Enum):
    PLANNED = "запланирован"
    CONFIRMED = "подтверждён"
    COMPLETED = "завершён"
    CANCELLED = "отменён"


# Допустимые переходы между статусами приёма
ALLOWED_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.PLANNED: {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED},
    AppointmentStatus.CONFIRMED: {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
}


@dataclass
class Entity:
    id: int


@dataclass
class Person(Entity):
    full_name: str

    def get_report_data(self) -> str:
        return f"{type(self).__name__} #{self.id}: {self.full_name}"


@dataclass
class Patient(Person):
    birth_year: int
    phone: str = ""

    def age(self, year: int | None = None) -> int:
        return (year or datetime.now().year) - self.birth_year

    def get_report_data(self) -> str:
        return f"Пациент #{self.id}: {self.full_name}, {self.age()} лет, тел. {self.phone or '—'}"


@dataclass
class Doctor(Person):
    specialty: str
    cabinet: int
    experience_years: int = 0

    def get_report_data(self) -> str:
        return (f"Врач #{self.id}: {self.full_name}, {self.specialty}, каб. {self.cabinet}, "
                f"стаж {self.experience_years} лет")


@dataclass
class Appointment(Entity):
    patient: Patient
    doctor: Doctor
    start: datetime
    duration_min: int
    status: AppointmentStatus = AppointmentStatus.PLANNED
    notes: list[str] = field(default_factory=list)

    def change_status(self, new_status: AppointmentStatus) -> None:
        from exceptions import InvalidStatusTransitionError
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStatusTransitionError(self.status, new_status)
        self.status = new_status

    def get_report_data(self) -> str:
        return (f"Приём #{self.id}: {self.start:%d.%m.%Y %H:%M}, {self.duration_min} мин, "
                f"{self.patient.full_name} -> {self.doctor.full_name} [{self.status.value}]")
