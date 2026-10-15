from dataclasses import replace

from exceptions import ConflictError, NotFoundError, ValidationError
from models import Appointment
from repository import AppointmentRepository
from schemas import validate

SORT_FIELDS = {"datetime": lambda a: (a.date, a.time), "doctor": lambda a: a.doctor,
               "cabinet": lambda a: a.cabinet, "id": lambda a: a.id}


class AppointmentService:
    def __init__(self, repository: AppointmentRepository) -> None:
        self.repository = repository

    def get_appointments(self, filters: dict | None = None, sort: str | None = None,
                         order: str = "asc") -> list[Appointment]:
        items = self.repository.get_all()
        for key, value in (filters or {}).items():
            if value:
                items = [a for a in items if str(getattr(a, key)).lower() == value.lower()]
        if sort:
            if sort not in SORT_FIELDS:
                raise ValidationError(f"Сортировка возможна по: {', '.join(SORT_FIELDS)}")
            if order not in ("asc", "desc"):
                raise ValidationError("order должен быть asc или desc")
            items = sorted(items, key=SORT_FIELDS[sort], reverse=order == "desc")
        return items

    def get_appointment(self, appointment_id: int) -> Appointment:
        appointment = self.repository.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError(f"Запись {appointment_id} не найдена")
        return appointment

    def _check_slot(self, candidate: Appointment) -> None:
        for other in self.repository.get_all():
            if (other.id != candidate.id and other.status != "cancelled"
                    and other.date == candidate.date and other.time == candidate.time
                    and (other.doctor == candidate.doctor or other.cabinet == candidate.cabinet)):
                raise ConflictError("Врач или кабинет уже заняты в это время")

    def _normalize(self, appointment: Appointment) -> Appointment:
        if appointment.patient and appointment.status == "free":
            appointment.status = "booked"
        if not appointment.patient and appointment.status in ("booked", "completed"):
            raise ValidationError("Для статуса booked/completed нужен пациент")
        return appointment

    def create_appointment(self, data) -> Appointment:
        fields = validate(data)
        candidate = self._normalize(Appointment(id=0, **fields))
        self._check_slot(candidate)
        return self.repository.create({k: v for k, v in candidate.to_dict().items() if k != "id"})

    def replace_appointment(self, appointment_id: int, data) -> Appointment:
        self.get_appointment(appointment_id)
        fields = validate(data)
        fields.setdefault("patient", "")
        fields.setdefault("status", "free")
        updated = self._normalize(Appointment(id=appointment_id, **fields))
        self._check_slot(updated)
        return self.repository.update(updated)

    def patch_appointment(self, appointment_id: int, data) -> Appointment:
        current = self.get_appointment(appointment_id)
        updated = self._normalize(replace(current, **validate(data, partial=True)))
        self._check_slot(updated)
        return self.repository.update(updated)

    def delete_appointment(self, appointment_id: int) -> None:
        if not self.repository.delete(appointment_id):
            raise NotFoundError(f"Запись {appointment_id} не найдена")

    def free_appointments(self, specialty: str | None = None, date: str | None = None) -> list:
        """Специализированная операция варианта: свободные записи."""
        return self.get_appointments({"status": "free", "specialty": specialty, "date": date},
                                     sort="datetime")
