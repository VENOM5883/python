"""Бизнес-логика системы записи на приём."""
import re
from datetime import datetime, time, timedelta

from src.exceptions import NotFoundError, SlotUnavailableError, ValidationError
from src.models.entities import Appointment, AppointmentStatus, Doctor, Patient

PHONE_RE = re.compile(r"^\+7\d{10}$")
OPEN, CLOSE = time(8, 0), time(20, 0)
MAX_DAYS_AHEAD = 30


def now() -> datetime:
    """Вынесено в функцию, чтобы в тестах подменять текущее время через patch."""
    return datetime.now()


def validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValidationError("ФИО не может быть пустым")
    if len(name) > 100:
        raise ValidationError("ФИО слишком длинное")
    return name


def validate_slot_minutes(minutes: int) -> int:
    if not isinstance(minutes, int) or not 10 <= minutes <= 120:
        raise ValidationError("Длительность приёма должна быть от 10 до 120 минут")
    return minutes


class ClinicService:
    def __init__(self, repository, notifier) -> None:
        self.repository = repository
        self.notifier = notifier

    def register_patient(self, full_name: str, phone: str) -> Patient:
        if not PHONE_RE.match(phone or ""):
            raise ValidationError("Телефон должен быть в формате +7XXXXXXXXXX")
        if self.repository.find_patient_by_phone(phone):
            raise ValidationError("Пациент с таким телефоном уже зарегистрирован")
        return self.repository.add_patient(Patient(None, validate_name(full_name), phone))

    def add_doctor(self, full_name: str, specialty: str, slot_minutes: int = 30) -> Doctor:
        if not (specialty or "").strip():
            raise ValidationError("Специальность обязательна")
        return self.repository.add_doctor(Doctor(None, validate_name(full_name), specialty.strip().lower(),
                                                 validate_slot_minutes(slot_minutes)))

    def _patient(self, patient_id: int) -> Patient:
        patient = self.repository.get_patient(patient_id)
        if patient is None:
            raise NotFoundError(f"Пациент {patient_id} не найден")
        return patient

    def _doctor(self, doctor_id: int) -> Doctor:
        doctor = self.repository.get_doctor(doctor_id)
        if doctor is None:
            raise NotFoundError(f"Врач {doctor_id} не найден")
        return doctor

    def create_appointment(self, patient_id: int, doctor_id: int, start: datetime) -> Appointment:
        if not isinstance(patient_id, int) or patient_id <= 0:
            raise ValidationError("Некорректный идентификатор пациента")
        patient, doctor = self._patient(patient_id), self._doctor(doctor_id)
        current = now()
        if start <= current:
            raise ValidationError("Нельзя записаться на прошедшее время")
        if start > current + timedelta(days=MAX_DAYS_AHEAD):
            raise ValidationError(f"Запись возможна не более чем на {MAX_DAYS_AHEAD} дней вперёд")
        end = start + timedelta(minutes=doctor.slot_minutes)
        if start.time() < OPEN or end.time() > CLOSE or end.date() != start.date():
            raise ValidationError("Время приёма вне рабочих часов (08:00–20:00)")
        for other in self.repository.doctor_appointments(doctor.id, start.date().isoformat()):
            other_end = other.start + timedelta(minutes=doctor.slot_minutes)
            if start < other_end and other.start < end:
                raise SlotUnavailableError(f"У врача {doctor.full_name} время {start:%H:%M} уже занято")
        appointment = self.repository.add_appointment(Appointment(None, patient.id, doctor.id, start))
        self.notifier.send(patient.phone, f"Вы записаны к {doctor.full_name} на {start:%d.%m.%Y %H:%M}")
        return appointment

    def cancel_appointment(self, appointment_id: int) -> Appointment:
        appointment = self.repository.get_appointment(appointment_id)
        if appointment is None:
            raise NotFoundError(f"Запись {appointment_id} не найдена")
        if appointment.status is not AppointmentStatus.BOOKED:
            raise ValidationError("Отменить можно только активную запись")
        self.repository.update_status(appointment_id, AppointmentStatus.CANCELLED)
        appointment.status = AppointmentStatus.CANCELLED
        patient = self._patient(appointment.patient_id)
        self.notifier.send(patient.phone, f"Запись на {appointment.start:%d.%m.%Y %H:%M} отменена")
        return appointment

    def free_slots(self, doctor_id: int, day: str) -> list[str]:
        doctor = self._doctor(doctor_id)
        busy = {a.start.strftime("%H:%M") for a in self.repository.doctor_appointments(doctor_id, day)}
        slots, cursor = [], datetime.combine(datetime.fromisoformat(day).date(), OPEN)
        while (cursor + timedelta(minutes=doctor.slot_minutes)).time() <= CLOSE and cursor.date().isoformat() == day:
            if cursor.strftime("%H:%M") not in busy:
                slots.append(cursor.strftime("%H:%M"))
            cursor += timedelta(minutes=doctor.slot_minutes)
        return slots

    def patient_history(self, patient_id: int) -> list[Appointment]:
        self._patient(patient_id)
        return self.repository.patient_appointments(patient_id)
