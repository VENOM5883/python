"""Лабораторная работа №14. REST API на FastAPI.
Вариант 15. Медицинская клиника — записи (/appointments).
Запуск: uvicorn app.main:app --reload  ->  http://127.0.0.1:8000/docs
"""
import logging
import time
from contextlib import asynccontextmanager
from datetime import date, time as dtime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, SessionLocal, engine
from app.models.appointment import Appointment
from app.routers.appointments import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("clinic-api")

SEED = [
    ("Иванов Иван Иванович", "Смирнова Е.В.", "терапевт", date(2026, 10, 20), dtime(9, 0), 101, "completed"),
    ("Петрова Анна Сергеевна", "Смирнова Е.В.", "терапевт", date(2026, 10, 20), dtime(9, 30), 101, "confirmed"),
    ("Сидоров Павел Олегович", "Кузнецов О.П.", "кардиолог", date(2026, 10, 20), dtime(10, 0), 205, "completed"),
    ("Новикова Ольга Дмитриевна", "Орлова Н.А.", "невролог", date(2026, 10, 21), dtime(12, 0), 310, "planned"),
    ("Фёдоров Максим Ильич", "Кузнецов О.П.", "кардиолог", date(2026, 10, 21), dtime(11, 0), 205, "cancelled"),
    ("Ковалёва Дарья Павловна", "Белова М.И.", "окулист", date(2026, 10, 22), dtime(14, 0), 120, "planned"),
    ("Иванов Иван Иванович", "Кузнецов О.П.", "кардиолог", date(2026, 10, 22), dtime(9, 0), 205, "planned"),
    ("Петрова Анна Сергеевна", "Орлова Н.А.", "невролог", date(2026, 10, 23), dtime(15, 30), 310, "confirmed"),
]


def seed() -> None:
    with SessionLocal() as session:
        if session.scalar(select(Appointment.id).limit(1)) is None:
            session.add_all(Appointment(patient=p, doctor=d, specialty=s, date=dt, time=t, cabinet=c,
                                        status=st) for p, d, s, dt, t, c, st in SEED)
            session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    seed()
    log.info("Application started")
    yield


app = FastAPI(title="Clinic Appointments API", version="1.0",
              description="Лабораторная работа №14, вариант 15: записи на приём в медицинскую клинику",
              lifespan=lifespan)
app.include_router(router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    log.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code,
             (time.perf_counter() - start) * 1000)
    return response


@app.exception_handler(SQLAlchemyError)
async def database_error(_: Request, exc: SQLAlchemyError):
    log.error("Database error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Database error"})


@app.get("/health", tags=["Служебные"])
async def health():
    return {"status": "healthy"}
