import datetime as dt

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("doctor", "date", "time", name="uq_doctor_slot"),
        CheckConstraint("cabinet > 0", name="ck_cabinet_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient: Mapped[str] = mapped_column(String(150), index=True)
    doctor: Mapped[str] = mapped_column(String(150), index=True)
    specialty: Mapped[str] = mapped_column(String(60), index=True)
    date: Mapped[dt.date]
    time: Mapped[dt.time]
    cabinet: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="planned")
