from enum import Enum


class AppointmentStatus(Enum):
    CREATED = "создан"
    CONFIRMED = "подтверждён"
    COMPLETED = "завершён"
    CANCELLED = "отменён"
