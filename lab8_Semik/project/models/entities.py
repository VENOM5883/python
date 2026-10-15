from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.enums import AppointmentStatus


@dataclass
class Appointment:
    """Базовая запись на приём."""
    id: int
    patient: str
    doctor: str
    start: datetime
    base_price: float = 0.0
    duration_min: int = 30
    price: float = 0.0
    status: AppointmentStatus = AppointmentStatus.CREATED

    @property
    def title(self) -> str:
        return "Приём"

    def describe(self) -> str:
        return (f"#{self.id} {self.title}: {self.patient} -> {self.doctor}, "
                f"{self.start:%d.%m.%Y %H:%M}, {self.duration_min} мин, {self.price:.2f} руб. "
                f"[{self.status.value}]")


@dataclass
class TherapyAppointment(Appointment):
    base_price: float = 1500.0
    duration_min: int = 30

    @property
    def title(self) -> str:
        return "Терапевтический приём"


@dataclass
class DiagnosticProcedure(Appointment):
    base_price: float = 3000.0
    duration_min: int = 45
    equipment: str = "УЗИ"

    @property
    def title(self) -> str:
        return f"Диагностическая процедура ({self.equipment})"


@dataclass
class Consultation(Appointment):
    base_price: float = 1000.0
    duration_min: int = 20
    online: bool = False

    @property
    def title(self) -> str:
        return "Онлайн-консультация" if self.online else "Консультация"
