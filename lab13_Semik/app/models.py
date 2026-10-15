"""Модель документа «приём» (appointment)."""
from dataclasses import asdict, dataclass, field
from datetime import datetime

STATUSES = ("planned", "confirmed", "completed", "cancelled")


@dataclass
class Appointment:
    patient: dict            # вложенный объект: {"full_name", "birth_year", "phone"}
    doctor: dict             # вложенный объект: {"id", "full_name", "specialty", "cabinet"}
    specialty: str
    date: str                # ГГГГ-ММ-ДД
    time: str                # ЧЧ:ММ
    status: str = "planned"
    diagnosis: str = ""
    prescriptions: list[str] = field(default_factory=list)   # массив назначений

    def validate(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"status должен быть одним из {STATUSES}")
        if not self.patient.get("full_name") or not self.doctor.get("full_name"):
            raise ValueError("Пациент и врач обязательны")
        datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")

    def to_document(self) -> dict:
        self.validate()
        return asdict(self)
