from datetime import datetime

from cache import ScheduleCache
from exceptions import ConflictError, NotFoundError, ValidationError
from repository import SORT_COLUMNS, AppointmentRepository

STATUSES = ("free", "booked", "completed", "cancelled")
FIELDS = {"doctor_id", "patient_id", "date", "time", "status"}


class AppointmentService:
    def __init__(self, repository: AppointmentRepository, cache: ScheduleCache) -> None:
        self.repository = repository
        self.cache = cache

    def _validate(self, data, partial: bool = False) -> dict:
        if not isinstance(data, dict):
            raise ValidationError("Тело запроса должно быть JSON-объектом")
        unknown = set(data) - FIELDS
        if unknown:
            raise ValidationError(f"Неизвестные поля: {', '.join(sorted(unknown))}")
        if not partial:
            missing = {"doctor_id", "date", "time"} - set(data)
            if missing:
                raise ValidationError(f"Отсутствуют поля: {', '.join(sorted(missing))}")
        if partial and not data:
            raise ValidationError("Нет полей для изменения")
        for key, fmt in (("date", "%Y-%m-%d"), ("time", "%H:%M")):
            if key in data:
                try:
                    datetime.strptime(str(data[key]), fmt)
                except ValueError:
                    raise ValidationError(f"Неверный формат поля {key}") from None
        if "status" in data and data["status"] not in STATUSES:
            raise ValidationError(f"status: одно из {', '.join(STATUSES)}")
        if "doctor_id" in data and not self.repository.exists("doctors", data["doctor_id"]):
            raise ValidationError(f"Врач {data['doctor_id']} не существует")
        if data.get("patient_id") is not None and not self.repository.exists("patients", data["patient_id"]):
            raise ValidationError(f"Пациент {data['patient_id']} не существует")
        result = dict(data)
        if result.get("patient_id") and result.get("status", "free") == "free":
            result["status"] = "booked"
        return result

    def list_appointments(self, filters: dict, sort: str | None, order: str) -> list[dict]:
        if (sort or "id") not in SORT_COLUMNS:
            raise ValidationError(f"Сортировка: {', '.join(SORT_COLUMNS)}")
        return self.repository.get_all(filters, sort or "id", order)

    def get(self, appointment_id: int) -> dict:
        appointment = self.repository.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError(f"Запись {appointment_id} не найдена")
        return appointment

    def _invalidate(self, appointment: dict) -> None:
        self.cache.invalidate(appointment["doctor_id"], appointment["date"])

    def create(self, data) -> dict:
        fields = self._validate(data)
        try:
            new_id = self.repository.create(fields)
        except Exception as error:  # sqlite3.IntegrityError — врач занят
            raise ConflictError(f"Слот уже существует: {error}") from error
        created = self.get(new_id)
        self._invalidate(created)
        return created

    def update(self, appointment_id: int, data, partial: bool) -> dict:
        before = self.get(appointment_id)
        fields = self._validate(data, partial)
        if not partial:
            fields.setdefault("patient_id", None)
            fields.setdefault("status", "booked" if fields["patient_id"] else "free")
        try:
            self.repository.update(appointment_id, fields)
        except Exception as error:
            raise ConflictError(f"Конфликт данных: {error}") from error
        after = self.get(appointment_id)
        self._invalidate(before)
        self._invalidate(after)
        return after

    def delete(self, appointment_id: int) -> None:
        appointment = self.get(appointment_id)
        self.repository.delete(appointment_id)
        self._invalidate(appointment)

    def free(self, specialty: str | None, date: str | None) -> list[dict]:
        return self.repository.get_all({"status": "free", "specialty": specialty, "date": date},
                                       "datetime")

    def schedule(self, doctor_id: int, date: str) -> dict:
        """Cache-aside: сначала Redis, при промахе — SQL и запись в Redis с TTL."""
        cached = self.cache.get(doctor_id, date)
        if cached is not None:
            return {"source": "redis", "ttl": self.cache.ttl(doctor_id, date), **cached}
        doctor = self.repository.doctor(doctor_id)
        if doctor is None:
            raise NotFoundError(f"Врач {doctor_id} не найден")
        data = {"doctor": doctor["full_name"], "date": date, "photo": doctor["photo"],
                "slots": self.repository.doctor_schedule(doctor_id, date)}
        self.cache.set(doctor_id, date, data)
        return {"source": "database", "ttl": self.cache.ttl(doctor_id, date), **data}

    def complete(self, appointment_id: int, services: list) -> dict:
        appointment = self.get(appointment_id)
        if not isinstance(services, list) or not services:
            raise ValidationError("Нужен непустой список services")
        try:
            total = self.repository.complete_with_services(appointment_id, services)
        except ValueError as error:
            raise ConflictError(str(error)) from error
        self._invalidate(appointment)
        return {**self.get(appointment_id), "total_cost": total}
