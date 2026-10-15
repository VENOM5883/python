from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class Patient:
    id: int | None
    full_name: str
    phone: str


@dataclass
class Doctor:
    id: int | None
    full_name: str
    specialty: str
    slot_minutes: int = 30


@dataclass
class Appointment:
    id: int | None
    patient_id: int
    doctor_id: int
    start: datetime
    status: AppointmentStatus = AppointmentStatus.BOOKED
