from datetime import datetime, timedelta

import pytest

from conftest import NOW, TOMORROW_10
from src.exceptions import NotFoundError, SlotUnavailableError, ValidationError
from src.models.entities import Appointment, AppointmentStatus, Patient


# ---------- регистрация пациента ----------
def test_register_patient_with_valid_data(service, repo_mock):
    # Arrange / Act
    patient = service.register_patient("Семик Алексей", "+79001234567")
    # Assert
    assert patient.id == 5
    repo_mock.add_patient.assert_called_once()
    assert repo_mock.add_patient.call_args.args[0].full_name == "Семик Алексей"


@pytest.mark.parametrize("phone", ["89001234567", "+7900123456", "", "+7900123456a", "+19001234567"])
def test_register_patient_invalid_phone(service, repo_mock, phone):
    with pytest.raises(ValidationError):
        service.register_patient("Семик Алексей", phone)
    repo_mock.add_patient.assert_not_called()


def test_register_patient_duplicate_phone(service, repo_mock):
    repo_mock.find_patient_by_phone.return_value = Patient(1, "Иванов Иван", "+79001112233")
    with pytest.raises(ValidationError, match="уже зарегистрирован"):
        service.register_patient("Другой Человек", "+79001112233")


# ---------- добавление врача ----------
def test_add_doctor_normalizes_specialty(service, repo_mock):
    doctor = service.add_doctor("Кузнецов О.П.", "  Кардиолог ", 40)
    assert doctor.specialty == "кардиолог" and doctor.slot_minutes == 40


def test_add_doctor_without_specialty(service):
    with pytest.raises(ValidationError):
        service.add_doctor("Кузнецов О.П.", "")


# ---------- создание записи ----------
def test_create_appointment_calls_repository_and_notifier(service, repo_mock, notifier, fixed_now):
    appointment = service.create_appointment(1, 2, TOMORROW_10)
    assert appointment.id == 10 and appointment.status is AppointmentStatus.BOOKED
    repo_mock.get_patient.assert_called_once_with(1)
    repo_mock.get_doctor.assert_called_once_with(2)
    repo_mock.doctor_appointments.assert_called_once_with(2, "2026-10-16")
    notifier.send.assert_called_once()
    assert notifier.send.call_args.args[0] == "+79001112233"


def test_create_appointment_double_booking_forbidden(service, repo_mock, notifier, fixed_now):
    repo_mock.doctor_appointments.return_value = [Appointment(3, 9, 2, TOMORROW_10 - timedelta(minutes=15))]
    with pytest.raises(SlotUnavailableError):
        service.create_appointment(1, 2, TOMORROW_10)
    repo_mock.add_appointment.assert_not_called()
    notifier.send.assert_not_called()


def test_adjacent_slot_is_allowed(service, repo_mock, fixed_now):
    repo_mock.doctor_appointments.return_value = [Appointment(3, 9, 2, TOMORROW_10 - timedelta(minutes=30))]
    assert service.create_appointment(1, 2, TOMORROW_10).id == 10


@pytest.mark.parametrize("start, message", [
    (NOW - timedelta(minutes=1), "прошедшее"),
    (NOW, "прошедшее"),
    (NOW + timedelta(days=31), "не более"),
    (datetime(2026, 10, 16, 7, 59), "рабочих"),
    (datetime(2026, 10, 16, 19, 31), "рабочих"),
])
def test_create_appointment_time_limits(service, fixed_now, start, message):
    with pytest.raises(ValidationError, match=message):
        service.create_appointment(1, 2, start)


def test_last_slot_of_the_day_is_allowed(service, fixed_now):
    assert service.create_appointment(1, 2, datetime(2026, 10, 16, 19, 30)).id == 10


def test_create_appointment_unknown_doctor(service, repo_mock, fixed_now):
    repo_mock.get_doctor.return_value = None
    with pytest.raises(NotFoundError):
        service.create_appointment(1, 99, TOMORROW_10)


@pytest.mark.parametrize("patient_id", [0, -1, "1"])
def test_create_appointment_invalid_patient_id(service, repo_mock, fixed_now, patient_id):
    with pytest.raises(ValidationError):
        service.create_appointment(patient_id, 2, TOMORROW_10)
    repo_mock.get_patient.assert_not_called()


# ---------- отмена ----------
def test_cancel_appointment(service, repo_mock, notifier):
    repo_mock.get_appointment.return_value = Appointment(10, 1, 2, TOMORROW_10)
    cancelled = service.cancel_appointment(10)
    assert cancelled.status is AppointmentStatus.CANCELLED
    repo_mock.update_status.assert_called_once_with(10, AppointmentStatus.CANCELLED)
    assert "отменена" in notifier.send.call_args.args[1]


def test_cancel_twice_forbidden(service, repo_mock):
    repo_mock.get_appointment.return_value = Appointment(10, 1, 2, TOMORROW_10, AppointmentStatus.CANCELLED)
    with pytest.raises(ValidationError):
        service.cancel_appointment(10)
    repo_mock.update_status.assert_not_called()


def test_cancel_missing(service, repo_mock):
    repo_mock.get_appointment.return_value = None
    with pytest.raises(NotFoundError):
        service.cancel_appointment(404)


# ---------- свободное время ----------
def test_free_slots_excludes_busy(service, repo_mock):
    repo_mock.doctor_appointments.return_value = [Appointment(1, 1, 2, datetime(2026, 10, 16, 8, 0))]
    slots = service.free_slots(2, "2026-10-16")
    assert slots[0] == "08:30" and slots[-1] == "19:30" and len(slots) == 23


def test_notifier_failure_is_visible(service, notifier, fixed_now):
    notifier.send.side_effect = ConnectionError("SMS-шлюз недоступен")
    with pytest.raises(ConnectionError):
        service.create_appointment(1, 2, TOMORROW_10)
