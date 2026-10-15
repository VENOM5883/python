"""Бизнес-логика клиники."""
from __future__ import annotations

from datetime import datetime, timedelta

from decorators import log_call, require_status, timer
from exceptions import EntityNotFoundError, ValidationError
from models import Appointment, AppointmentStatus, Doctor, Patient


class ClinicService:
    def __init__(self) -> None:
        self.patients: dict[int, Patient] = {}
        self.doctors: dict[int, Doctor] = {}
        self.appointments: dict[int, Appointment] = {}
        self._next_id = 1

    def _new_id(self) -> int:
        self._next_id += 1
        return self._next_id - 1

    @log_call
    def add_patient(self, full_name: str, birth_year: int, phone: str = "") -> Patient:
        """Регистрирует нового пациента."""
        if not full_name.strip():
            raise ValidationError("ФИО пациента не может быть пустым")
        if not 1900 <= birth_year <= datetime.now().year:
            raise ValidationError("Некорректный год рождения")
        patient = Patient(self._new_id(), full_name.strip(), birth_year, phone)
        self.patients[patient.id] = patient
        return patient

    @log_call
    def add_doctor(self, full_name: str, specialty: str, cabinet: int,
                   experience_years: int = 0) -> Doctor:
        if not full_name.strip() or not specialty.strip():
            raise ValidationError("ФИО и специальность обязательны")
        doctor = Doctor(self._new_id(), full_name.strip(), specialty.strip(), cabinet,
                        experience_years)
        self.doctors[doctor.id] = doctor
        return doctor

    def get_patient(self, patient_id: int) -> Patient:
        if patient_id not in self.patients:
            raise EntityNotFoundError("Пациент", patient_id)
        return self.patients[patient_id]

    def get_doctor(self, doctor_id: int) -> Doctor:
        if doctor_id not in self.doctors:
            raise EntityNotFoundError("Врач", doctor_id)
        return self.doctors[doctor_id]

    def get_appointment(self, appointment_id: int) -> Appointment:
        if appointment_id not in self.appointments:
            raise EntityNotFoundError("Приём", appointment_id)
        return self.appointments[appointment_id]

    @log_call
    def create_appointment(self, patient_id: int, doctor_id: int, start: datetime,
                           duration_min: int = 30) -> Appointment:
        patient, doctor = self.get_patient(patient_id), self.get_doctor(doctor_id)
        if duration_min <= 0:
            raise ValidationError("Длительность приёма должна быть положительной")
        end = start + timedelta(minutes=duration_min)
        for other in self.find_by_doctor(doctor_id):
            if other.status is AppointmentStatus.CANCELLED:
                continue
            other_end = other.start + timedelta(minutes=other.duration_min)
            if start < other_end and other.start < end:
                raise ValidationError(f"У врача {doctor.full_name} это время занято")
        appointment = Appointment(self._new_id(), patient, doctor, start, duration_min)
        self.appointments[appointment.id] = appointment
        return appointment

    def delete(self, entity_id: int) -> None:
        for storage in (self.appointments, self.patients, self.doctors):
            if entity_id in storage:
                del storage[entity_id]
                return
        raise EntityNotFoundError("Объект", entity_id)

    def change_status(self, appointment_id: int, status: AppointmentStatus) -> Appointment:
        appointment = self.get_appointment(appointment_id)
        appointment.change_status(status)
        return appointment

    @require_status(AppointmentStatus.CONFIRMED)
    def complete_appointment(self, appointment_id: int, conclusion: str) -> Appointment:
        appointment = self.get_appointment(appointment_id)
        appointment.notes.append(conclusion)
        appointment.change_status(AppointmentStatus.COMPLETED)
        return appointment

    def find_by_doctor(self, doctor_id: int) -> list[Appointment]:
        return [a for a in self.appointments.values() if a.doctor.id == doctor_id]

    def find_by_name(self, text: str) -> list:
        text = text.lower()
        people = list(self.patients.values()) + list(self.doctors.values())
        return [p for p in people if text in p.full_name.lower()]

    # --- специализированные операции варианта ---
    def count_appointments_by_doctor(self) -> dict[str, int]:
        return {d.full_name: sum(1 for a in self.appointments.values()
                                 if a.doctor.id == d.id and a.status is not AppointmentStatus.CANCELLED)
                for d in self.doctors.values()}

    def average_duration(self) -> float:
        durations = [a.duration_min for a in self.appointments.values()
                     if a.status is not AppointmentStatus.CANCELLED]
        if not durations:
            raise ZeroDivisionError("Нет приёмов для расчёта средней продолжительности")
        return sum(durations) / len(durations)

    @timer
    def statistics(self) -> dict[str, float | int]:
        appointments = list(self.appointments.values())
        by_status = {s.value: sum(1 for a in appointments if a.status is s)
                     for s in AppointmentStatus}
        durations = [a.duration_min for a in appointments]
        return {
            "пациентов": len(self.patients),
            "врачей": len(self.doctors),
            "приёмов": len(appointments),
            **by_status,
            "средняя длительность, мин": round(sum(durations) / len(durations), 1) if durations else 0,
            "минимальная длительность": min(durations, default=0),
            "максимальная длительность": max(durations, default=0),
        }


def create_demo_clinic() -> ClinicService:
    import builtins
    original_print = builtins.print
    builtins.print = lambda *a, **k: None  # не засоряем вывод журналом при заполнении
    try:
        clinic = ClinicService()
        p1 = clinic.add_patient("Иванов Иван Иванович", 1985, "+7-900-111-22-33")
        p2 = clinic.add_patient("Петрова Анна Сергеевна", 1992, "+7-900-222-33-44")
        p3 = clinic.add_patient("Сидоров Павел Олегович", 1970)
        d1 = clinic.add_doctor("Смирнова Елена Викторовна", "терапевт", 101, 12)
        d2 = clinic.add_doctor("Кузнецов Олег Петрович", "кардиолог", 205, 20)
        base = datetime(2026, 10, 20, 9, 0)
        a1 = clinic.create_appointment(p1.id, d1.id, base, 30)
        clinic.create_appointment(p2.id, d1.id, base + timedelta(minutes=30), 20)
        a3 = clinic.create_appointment(p3.id, d2.id, base, 45)
        clinic.create_appointment(p1.id, d2.id, base + timedelta(hours=1), 40)
        clinic.change_status(a1.id, AppointmentStatus.CONFIRMED)
        clinic.change_status(a3.id, AppointmentStatus.CONFIRMED)
        clinic.complete_appointment(a3.id, "Рекомендовано ЭКГ через месяц")
    finally:
        builtins.print = original_print
    return clinic
