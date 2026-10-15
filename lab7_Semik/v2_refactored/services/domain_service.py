"""Сервисы: каждый отвечает за одну задачу и получает зависимости извне (SRP, DIP)."""
from __future__ import annotations

from datetime import datetime

from interfaces.repository import Readable, Repository
from interfaces.services import Notifier, Procedure
from models.entities import Appointment, Doctor, Patient
from models.enums import AppointmentStatus


class ClinicError(Exception):
    pass


class PatientService:
    def __init__(self, patients: Repository[Patient], notifier: Notifier) -> None:
        self.patients = patients
        self.notifier = notifier

    def register(self, full_name: str, phone: str = "") -> Patient:
        if not full_name.strip():
            raise ClinicError("ФИО пациента не может быть пустым")
        patient = self.patients.add(Patient(self.patients.next_id(), full_name.strip(), phone))
        self.notifier.send(patient.full_name, "Вы зарегистрированы в клинике")
        return patient


class AppointmentService:
    """Медицинская логика: запись, назначение врача, проведение приёма."""

    def __init__(self, appointments: Repository[Appointment], patients: Readable[Patient],
                 doctors: Readable[Doctor], notifier: Notifier) -> None:
        self.appointments = appointments
        self.patients = patients
        self.doctors = doctors
        self.notifier = notifier

    def _patient(self, patient_id: int) -> Patient:
        patient = self.patients.get(patient_id)
        if patient is None:
            raise ClinicError(f"Пациент {patient_id} не найден")
        return patient

    def _appointment(self, appointment_id: int) -> Appointment:
        appointment = self.appointments.get(appointment_id)
        if appointment is None:
            raise ClinicError(f"Запись {appointment_id} не найдена")
        return appointment

    def book(self, patient_id: int, start: datetime) -> Appointment:
        patient = self._patient(patient_id)
        appointment = Appointment(self.appointments.next_id(), patient.id, start)
        appointment.history.append("запись создана")
        self.appointments.add(appointment)
        self.notifier.send(patient.full_name, f"Вы записаны на {start:%d.%m.%Y %H:%M}")
        return appointment

    def assign_doctor(self, appointment_id: int, doctor_id: int) -> Appointment:
        appointment = self._appointment(appointment_id)
        doctor = self.doctors.get(doctor_id)
        if doctor is None:
            raise ClinicError(f"Врач {doctor_id} не найден")
        busy = any(a.doctor_id == doctor_id and a.start == appointment.start and a.id != appointment.id
                   and a.status is not AppointmentStatus.CANCELLED
                   for a in self.appointments.get_all())
        if busy:
            raise ClinicError(f"У врача {doctor.full_name} это время занято")
        appointment.doctor_id = doctor_id
        appointment.status = AppointmentStatus.ASSIGNED
        appointment.history.append(f"назначен врач {doctor.full_name}")
        self.appointments.add(appointment)
        return appointment

    def conduct(self, appointment_id: int, procedure: Procedure) -> Appointment:
        appointment = self._appointment(appointment_id)
        if appointment.status is not AppointmentStatus.ASSIGNED:
            raise ClinicError("Приём можно провести только после назначения врача")
        patient = self._patient(appointment.patient_id)
        appointment.procedure = procedure.title
        appointment.result = procedure.perform(patient.full_name)
        appointment.price = procedure.price()
        appointment.status = AppointmentStatus.COMPLETED
        appointment.history.append("приём проведён")
        self.appointments.add(appointment)
        self.notifier.send(patient.full_name, f"Результат: {appointment.result}. "
                                              f"К оплате {appointment.price:.0f} руб.")
        return appointment


class ReportService:
    """Формирование результатов — только чтение данных."""

    def __init__(self, appointments: Readable[Appointment], patients: Readable[Patient],
                 doctors: Readable[Doctor]) -> None:
        self.appointments = appointments
        self.patients = patients
        self.doctors = doctors

    def build_result(self, appointment_id: int) -> str:
        a = self.appointments.get(appointment_id)
        if a is None:
            raise ClinicError(f"Запись {appointment_id} не найдена")
        patient = self.patients.get(a.patient_id)
        doctor = self.doctors.get(a.doctor_id) if a.doctor_id else None
        return (f"Приём №{a.id} от {a.start:%d.%m.%Y %H:%M}\n"
                f"Пациент: {patient.full_name}\nВрач: {doctor.full_name if doctor else '—'}\n"
                f"Вид: {a.procedure or '—'}\nСтатус: {a.status.value}\n"
                f"Результат: {a.result or '—'}\nСтоимость: {a.price:.2f} руб.")

    def summary(self) -> dict[str, float]:
        items = self.appointments.get_all()
        done = [a for a in items if a.status is AppointmentStatus.COMPLETED]
        return {"всего записей": len(items), "проведено": len(done),
                "выручка": sum(a.price for a in done)}
