from enum import Enum


class AppointmentStatus(Enum):
    PLANNED = "planned"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
