"""Интеграционные тесты: Service -> Repository -> SQLite (без Mock-репозитория)."""
from datetime import datetime

import pytest

from conftest import TOMORROW_10
from src.exceptions import SlotUnavailableError
from src.models.entities import AppointmentStatus
from src.repositories.sqlite_repository import ClinicRepository


def test_full_booking_scenario(real_service, fixed_now):
    patient = real_service.register_patient("Семик Алексей", "+79001234567")
    doctor = real_service.add_doctor("Смирнова Е.В.", "терапевт", 30)
    appointment = real_service.create_appointment(patient.id, doctor.id, TOMORROW_10)
    stored = real_service.repository.get_appointment(appointment.id)
    assert stored.start == TOMORROW_10 and stored.status is AppointmentStatus.BOOKED
    assert "10:00" not in real_service.free_slots(doctor.id, "2026-10-16")


def test_double_booking_in_database(real_service, fixed_now):
    first = real_service.register_patient("Первый Пациент", "+79000000001")
    second = real_service.register_patient("Второй Пациент", "+79000000002")
    doctor = real_service.add_doctor("Кузнецов О.П.", "кардиолог", 40)
    real_service.create_appointment(first.id, doctor.id, TOMORROW_10)
    with pytest.raises(SlotUnavailableError):
        real_service.create_appointment(second.id, doctor.id, datetime(2026, 10, 16, 10, 20))
    real_service.cancel_appointment(1)
    assert real_service.create_appointment(second.id, doctor.id, datetime(2026, 10, 16, 10, 20)).id == 2
    assert [a.status for a in real_service.patient_history(first.id)] == [AppointmentStatus.CANCELLED]


def test_repository_on_disk(tmp_path):
    path = str(tmp_path / "clinic.db")
    from src.models.entities import Doctor
    writer = ClinicRepository(path)
    writer.add_doctor(Doctor(None, "Белова М.И.", "окулист"))
    writer.close()
    reader = ClinicRepository(path)
    assert [d.full_name for d in reader.doctors_by_specialty("окулист")] == ["Белова М.И."]
    reader.close()
