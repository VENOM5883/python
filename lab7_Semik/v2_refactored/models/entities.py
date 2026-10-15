"""Сущности предметной области. Иерархия не обещает лишнего поведения (LSP)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from models.enums import AppointmentStatus


@dataclass
class Person:
    id: int
    full_name: str


@dataclass
class Patient(Person):
    phone: str = ""


@dataclass
class Doctor(Person):
    specialty: str = "терапевт"

    def prescribe(self, patient: Patient, medicine: str) -> str:
        return f"{self.full_name} назначил {medicine} пациенту {patient.full_name}"


@dataclass
class Appointment:
    id: int
    patient_id: int
    start: datetime
    doctor_id: int | None = None
    status: AppointmentStatus = AppointmentStatus.PLANNED
    procedure: str = ""
    result: str = ""
    price: float = 0.0
    history: list[str] = field(default_factory=list)
