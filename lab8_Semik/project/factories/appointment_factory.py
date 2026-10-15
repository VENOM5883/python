"""Factory: создание записей разных типов сосредоточено в одном месте."""
from datetime import datetime

from models.entities import Appointment, Consultation, DiagnosticProcedure, TherapyAppointment


class AppointmentFactory:
    _types: dict[str, type[Appointment]] = {
        "therapy": TherapyAppointment,
        "diagnostics": DiagnosticProcedure,
        "consultation": Consultation,
    }

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._types)

    @classmethod
    def create(cls, kind: str, appointment_id: int, patient: str, doctor: str,
               start: datetime, **extra) -> Appointment:
        if kind not in cls._types:
            raise ValueError(f"Неизвестный тип приёма: {kind}")
        return cls._types[kind](appointment_id, patient, doctor, start, **extra)
