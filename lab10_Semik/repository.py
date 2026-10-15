from models import Appointment


class AppointmentRepository:
    """Хранение записей в памяти."""

    def __init__(self) -> None:
        self._items: dict[int, Appointment] = {}
        self._next_id = 1

    def get_all(self) -> list[Appointment]:
        return list(self._items.values())

    def get_by_id(self, appointment_id: int) -> Appointment | None:
        return self._items.get(appointment_id)

    def create(self, data: dict) -> Appointment:
        appointment = Appointment(id=self._next_id, **data)
        self._items[appointment.id] = appointment
        self._next_id += 1
        return appointment

    def update(self, appointment: Appointment) -> Appointment:
        self._items[appointment.id] = appointment
        return appointment

    def delete(self, appointment_id: int) -> bool:
        return self._items.pop(appointment_id, None) is not None
