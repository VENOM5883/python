from datetime import datetime

import pytest

from models.entities import Appointment, Doctor, Patient
from models.enums import AppointmentStatus
from procedures.procedures import ConsultationProcedure, DiagnosticsProcedure, VaccinationProcedure
from repositories.file_repository import FileRepository
from repositories.memory_repository import InMemoryRepository
from services.domain_service import AppointmentService, ClinicError, PatientService, ReportService

START = datetime(2026, 10, 20, 9, 0)


class FakeNotifier:
    def __init__(self):
        self.messages = []

    def send(self, recipient, message):
        self.messages.append((recipient, message))


def make_services(patients=None, doctors=None, appointments=None):
    patients = patients or InMemoryRepository()
    doctors = doctors or InMemoryRepository()
    appointments = appointments or InMemoryRepository()
    doctors.add(Doctor(1, "Смирнова Е.В.", "терапевт"))
    notifier = FakeNotifier()
    return (PatientService(patients, notifier),
            AppointmentService(appointments, patients, doctors, notifier),
            ReportService(appointments, patients, doctors), notifier)


def test_register_patient_sends_notification():
    patient_service, _, _, notifier = make_services()
    patient = patient_service.register("Иванов И.И.")
    assert patient.id == 1
    assert notifier.messages[0][0] == "Иванов И.И."


def test_register_empty_name_fails():
    patient_service, *_ = make_services()
    with pytest.raises(ClinicError):
        patient_service.register("   ")


def test_full_scenario_book_assign_conduct_result():
    patient_service, appointments, reports, _ = make_services()
    patient = patient_service.register("Иванов И.И.")
    appointment = appointments.book(patient.id, START)
    appointments.assign_doctor(appointment.id, 1)
    done = appointments.conduct(appointment.id, DiagnosticsProcedure())
    assert done.status is AppointmentStatus.COMPLETED
    assert done.price == 3000
    assert "Смирнова" in reports.build_result(appointment.id)


def test_cannot_conduct_without_doctor():
    patient_service, appointments, _, _ = make_services()
    patient = patient_service.register("Петрова А.С.")
    appointment = appointments.book(patient.id, START)
    with pytest.raises(ClinicError):
        appointments.conduct(appointment.id, ConsultationProcedure())


def test_doctor_cannot_be_double_booked():
    patient_service, appointments, _, _ = make_services()
    first = appointments.book(patient_service.register("А").id, START)
    second = appointments.book(patient_service.register("Б").id, START)
    appointments.assign_doctor(first.id, 1)
    with pytest.raises(ClinicError):
        appointments.assign_doctor(second.id, 1)


def test_new_procedure_without_changing_service():
    patient_service, appointments, reports, _ = make_services()
    appointment = appointments.book(patient_service.register("В").id, START)
    appointments.assign_doctor(appointment.id, 1)
    appointments.conduct(appointment.id, VaccinationProcedure())
    assert reports.summary()["выручка"] == 800


def test_file_repository_is_substitutable(tmp_path):
    patients = FileRepository(tmp_path / "p.json", Patient)
    doctors = FileRepository(tmp_path / "d.json", Doctor)
    appointments = FileRepository(tmp_path / "a.json", Appointment)
    patient_service, service, _, _ = make_services(patients, doctors, appointments)
    appointment = service.book(patient_service.register("Г").id, START)
    service.assign_doctor(appointment.id, 1)
    reloaded = FileRepository(tmp_path / "a.json", Appointment).get(appointment.id)
    assert reloaded.status is AppointmentStatus.ASSIGNED
    assert reloaded.start == START
