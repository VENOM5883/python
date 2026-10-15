"""Бизнес-логика клиники. Не зависит от Telegram. Блокирующие обращения к SQLite
выполняются в отдельном потоке (asyncio.to_thread), чтобы не останавливать event loop."""
import asyncio
import re
import sqlite3
from datetime import date, datetime

from database.repository import ClinicRepository

WORK_HOURS = [f"{h:02d}:{m:02d}" for h in range(9, 17) for m in (0, 30)]
PHONE_RE = re.compile(r"^\+7\d{10}$")


class ClinicError(Exception):
    """Ошибка, текст которой можно показать пользователю."""


def validate_name(text: str) -> str:
    text = (text or "").strip()
    if len(text.split()) < 2 or not all(part.replace("-", "").isalpha() for part in text.split()):
        raise ClinicError("Введите фамилию и имя буквами, например: Иванов Иван")
    return text


def validate_phone(text: str) -> str:
    phone = re.sub(r"[\s()-]", "", text or "")
    if phone.startswith("8"):
        phone = "+7" + phone[1:]
    if not PHONE_RE.match(phone):
        raise ClinicError("Телефон должен быть в формате +7XXXXXXXXXX")
    return phone


def validate_date(text: str, today: date | None = None) -> str:
    try:
        value = datetime.strptime((text or "").strip(), "%d.%m.%Y").date()
    except ValueError:
        raise ClinicError("Дата должна быть в формате ДД.ММ.ГГГГ, например 25.10.2026") from None
    today = today or date.today()
    if value < today:
        raise ClinicError("Нельзя записаться на прошедшую дату")
    if value.weekday() == 6:
        raise ClinicError("В воскресенье клиника не работает")
    if (value - today).days > 60:
        raise ClinicError("Запись открыта не более чем на 60 дней вперёд")
    return value.isoformat()


class ClinicService:
    def __init__(self, repository: ClinicRepository) -> None:
        self.repository = repository

    async def _run(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    async def specialties(self) -> list[str]:
        return await self._run(self.repository.specialties)

    async def doctors(self, specialty: str | None = None) -> list[dict]:
        return await self._run(self.repository.doctors, specialty)

    async def doctor(self, doctor_id: int) -> dict:
        doctor = await self._run(self.repository.doctor, doctor_id)
        if doctor is None:
            raise ClinicError("Врач не найден")
        return doctor

    async def search_doctors(self, text: str) -> list[dict]:
        if len(text.strip()) < 2:
            raise ClinicError("Введите минимум 2 символа для поиска")
        return await self._run(self.repository.search_doctors, text.strip())

    async def get_patient(self, telegram_id: int) -> dict | None:
        return await self._run(self.repository.patient_by_telegram, telegram_id)

    async def register(self, telegram_id: int, full_name: str, phone: str) -> dict:
        try:
            return await self._run(self.repository.create_patient, telegram_id,
                                   validate_name(full_name), validate_phone(phone))
        except sqlite3.IntegrityError:
            raise ClinicError("Вы уже зарегистрированы") from None

    async def free_times(self, doctor_id: int, date_iso: str) -> list[str]:
        busy = await self._run(self.repository.busy_times, doctor_id, date_iso)
        return [t for t in WORK_HOURS if t not in busy]

    async def book(self, telegram_id: int, doctor_id: int, date_iso: str, time: str, complaint: str) -> dict:
        patient = await self.get_patient(telegram_id)
        if patient is None:
            raise ClinicError("Сначала зарегистрируйтесь")
        if time not in await self.free_times(doctor_id, date_iso):
            raise ClinicError("Это время уже занято, выберите другое")
        try:
            appointment_id = await self._run(self.repository.create_appointment, patient["id"], doctor_id,
                                             date_iso, time, complaint.strip()[:200])
        except sqlite3.IntegrityError:
            raise ClinicError("Это время уже занято, выберите другое") from None
        return await self._run(self.repository.appointment, appointment_id)

    async def _own_appointment(self, telegram_id: int, appointment_id: int) -> dict:
        patient = await self.get_patient(telegram_id)
        appointment = await self._run(self.repository.appointment, appointment_id)
        if patient is None or appointment is None or appointment["patient_id"] != patient["id"]:
            raise ClinicError("Запись не найдена")
        return appointment

    async def my_appointments(self, telegram_id: int) -> list[dict]:
        patient = await self.get_patient(telegram_id)
        return [] if patient is None else await self._run(
            self.repository.patient_appointments, patient["id"], ("planned",))

    async def history(self, telegram_id: int) -> list[dict]:
        patient = await self.get_patient(telegram_id)
        return [] if patient is None else await self._run(
            self.repository.patient_appointments, patient["id"], ("completed", "cancelled"))

    async def appointment(self, telegram_id: int, appointment_id: int) -> dict:
        return await self._own_appointment(telegram_id, appointment_id)

    async def change_complaint(self, telegram_id: int, appointment_id: int, complaint: str) -> dict:
        appointment = await self._own_appointment(telegram_id, appointment_id)
        if appointment["status"] != "planned":
            raise ClinicError("Изменить можно только запланированную запись")
        if not complaint.strip():
            raise ClinicError("Жалоба не может быть пустой")
        await self._run(self.repository.update_appointment, appointment_id, complaint=complaint.strip()[:200])
        return await self._run(self.repository.appointment, appointment_id)

    async def cancel(self, telegram_id: int, appointment_id: int) -> None:
        appointment = await self._own_appointment(telegram_id, appointment_id)
        if appointment["status"] != "planned":
            raise ClinicError("Отменить можно только запланированную запись")
        await self._run(self.repository.update_appointment, appointment_id, status="cancelled")

    async def delete(self, telegram_id: int, appointment_id: int) -> None:
        appointment = await self._own_appointment(telegram_id, appointment_id)
        if appointment["status"] == "planned":
            raise ClinicError("Сначала отмените запись")
        await self._run(self.repository.delete_appointment, appointment_id)

    async def statistics(self) -> dict:
        return await self._run(self.repository.counts)
