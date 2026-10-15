from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment

SORT_FIELDS = {"date": (Appointment.date, Appointment.time), "doctor": (Appointment.doctor,),
               "patient": (Appointment.patient,), "cabinet": (Appointment.cabinet,),
               "id": (Appointment.id,)}


class AppointmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _filtered(self, filters: dict):
        stmt = select(Appointment)
        for key, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(Appointment, key) == value)
        return stmt

    def list(self, filters: dict, sort: str, order: str, skip: int, limit: int):
        stmt = self._filtered(filters)
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        columns = [c.desc() if order == "desc" else c.asc() for c in SORT_FIELDS[sort]]
        items = self.session.scalars(stmt.order_by(*columns).offset(skip).limit(limit)).all()
        return list(items), total

    def get(self, appointment_id: int) -> Appointment | None:
        return self.session.get(Appointment, appointment_id)

    def add(self, appointment: Appointment) -> Appointment:
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment

    def save(self, appointment: Appointment) -> Appointment:
        self.session.commit()
        self.session.refresh(appointment)
        return appointment

    def delete(self, appointment: Appointment) -> None:
        self.session.delete(appointment)
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def search(self, query: str, limit: int) -> list[Appointment]:
        pattern = f"%{query}%"
        stmt = (select(Appointment)
                .where(or_(Appointment.patient.ilike(pattern), Appointment.doctor.ilike(pattern),
                           Appointment.specialty.ilike(pattern)))
                .order_by(Appointment.date, Appointment.time).limit(limit))
        return list(self.session.scalars(stmt))

    def count_by(self, column) -> dict[str, int]:
        rows = self.session.execute(select(column, func.count()).group_by(column)).all()
        return {str(key): count for key, count in rows}
