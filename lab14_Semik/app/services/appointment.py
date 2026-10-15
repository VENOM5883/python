from __future__ import annotations

from collections import Counter

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.cache import AppointmentCache
from app.models.appointment import Appointment
from app.repositories.appointment import SORT_FIELDS, AppointmentRepository
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate


class AppointmentService:
    def __init__(self, repository: AppointmentRepository, cache: AppointmentCache) -> None:
        self.repository = repository
        self.cache = cache
        self.last_source = ""

    def _get_or_404(self, appointment_id: int) -> Appointment:
        appointment = self.repository.get(appointment_id)
        if appointment is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Appointment {appointment_id} not found")
        return appointment

    def _save(self, action):
        try:
            return action()
        except IntegrityError:
            self.repository.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT,
                                "У врача уже есть запись на это время") from None

    def list(self, filters, sort, order, skip, limit):
        if sort not in SORT_FIELDS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"sort must be one of: {', '.join(SORT_FIELDS)}")
        return self.repository.list(filters, sort, order, skip, limit)

    def get(self, appointment_id: int) -> dict:
        cached = self.cache.get(appointment_id)
        if cached is not None:
            self.last_source = "cache"
            return cached
        data = AppointmentResponse.model_validate(self._get_or_404(appointment_id)).model_dump(mode="json")
        self.cache.set(appointment_id, data)
        self.last_source = "database"
        return data

    def create(self, payload: AppointmentCreate) -> Appointment:
        return self._save(lambda: self.repository.add(Appointment(**payload.model_dump())))

    def replace(self, appointment_id: int, payload: AppointmentCreate) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        for key, value in payload.model_dump().items():
            setattr(appointment, key, value)
        result = self._save(lambda: self.repository.save(appointment))
        self.cache.invalidate(appointment_id)
        return result

    def patch(self, appointment_id: int, payload: AppointmentUpdate) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No fields to update")
        for key, value in changes.items():
            if value is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Field {key} cannot be null")
            setattr(appointment, key, value)
        result = self._save(lambda: self.repository.save(appointment))
        self.cache.invalidate(appointment_id)
        return result

    def delete(self, appointment_id: int) -> None:
        self.repository.delete(self._get_or_404(appointment_id))
        self.cache.invalidate(appointment_id)

    def search(self, query: str, limit: int):
        return self.repository.search(query, limit)

    def statistics(self) -> dict:
        by_status = self.repository.count_by(Appointment.status)
        doctors = Counter(self.repository.count_by(Appointment.doctor))
        total = sum(by_status.values())
        return {"total": total, "by_status": by_status,
                "by_specialty": self.repository.count_by(Appointment.specialty),
                "busiest_doctor": doctors.most_common(1)[0][0] if doctors else None,
                "completed_share": round(by_status.get("completed", 0) / total, 3) if total else 0.0}
