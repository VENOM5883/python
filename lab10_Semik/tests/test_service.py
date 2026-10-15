import pytest

from exceptions import ConflictError, NotFoundError, ValidationError
from repository import AppointmentRepository
from service import AppointmentService


@pytest.fixture
def service():
    return AppointmentService(AppointmentRepository())


def test_patient_makes_slot_booked(service, new_slot):
    appointment = service.create_appointment({**new_slot, "patient": "Иванов"})
    assert appointment.status == "booked"


def test_conflict_same_doctor_time(service, new_slot):
    service.create_appointment(new_slot)
    with pytest.raises(ConflictError):
        service.create_appointment({**new_slot, "cabinet": 999})


def test_validation_and_not_found(service, new_slot):
    with pytest.raises(ValidationError):
        service.create_appointment({**new_slot, "cabinet": -1})
    with pytest.raises(NotFoundError):
        service.get_appointment(100)
