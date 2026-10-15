"""Pydantic-схемы запросов и ответов."""
import datetime as dt
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    planned = "planned"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class AppointmentBase(BaseModel):
    patient: str = Field(min_length=2, max_length=150, examples=["Иванов Иван Иванович"])
    doctor: str = Field(min_length=2, max_length=150, examples=["Смирнова Е.В."])
    specialty: str = Field(min_length=2, max_length=60, examples=["терапевт"])
    date: dt.date
    time: dt.time
    cabinet: int = Field(gt=0, lt=10000, examples=[101])
    status: Status = Status.planned


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient: str | None = Field(default=None, min_length=2, max_length=150)
    doctor: str | None = Field(default=None, min_length=2, max_length=150)
    specialty: str | None = Field(default=None, min_length=2, max_length=60)
    date: dt.date | None = None
    time: dt.time | None = None
    cabinet: int | None = Field(default=None, gt=0, lt=10000)
    status: Status | None = None


class AppointmentResponse(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    total: int
    skip: int
    limit: int


class Statistics(BaseModel):
    total: int
    by_status: dict[str, int]
    by_specialty: dict[str, int]
    busiest_doctor: str | None
    completed_share: float
