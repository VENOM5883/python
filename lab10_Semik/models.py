from dataclasses import asdict, dataclass

STATUSES = ("free", "booked", "completed", "cancelled")


@dataclass
class Appointment:
    id: int
    doctor: str
    specialty: str
    date: str        # ГГГГ-ММ-ДД
    time: str        # ЧЧ:ММ
    cabinet: int
    patient: str = ""
    status: str = "free"

    def to_dict(self) -> dict:
        return asdict(self)
