import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.entities import Appointment, Doctor, Patient  # noqa: E402
from src.repositories.sqlite_repository import ClinicRepository  # noqa: E402
from src.services.clinic_service import ClinicService  # noqa: E402

NOW = datetime(2026, 10, 15, 12, 0)
TOMORROW_10 = datetime(2026, 10, 16, 10, 0)


@pytest.fixture
def fixed_now():
    """Фиксируем «текущее время», чтобы тесты не зависели от даты запуска."""
    with patch("src.services.clinic_service.now", return_value=NOW) as mocked:
        yield mocked


@pytest.fixture
def repo_mock():
    repository = Mock()
    repository.get_patient.return_value = Patient(1, "Иванов Иван", "+79001112233")
    repository.get_doctor.return_value = Doctor(2, "Смирнова Е.В.", "терапевт", 30)
    repository.find_patient_by_phone.return_value = None
    repository.doctor_appointments.return_value = []
    repository.add_appointment.side_effect = lambda a: Appointment(10, a.patient_id, a.doctor_id, a.start)
    repository.add_patient.side_effect = lambda p: Patient(5, p.full_name, p.phone)
    repository.add_doctor.side_effect = lambda d: Doctor(7, d.full_name, d.specialty, d.slot_minutes)
    return repository


@pytest.fixture
def notifier():
    return Mock()


@pytest.fixture
def service(repo_mock, notifier):
    return ClinicService(repo_mock, notifier)


@pytest.fixture
def real_service(notifier):
    """Для интеграционных тестов: настоящий SQLite-репозиторий (в памяти)."""
    repository = ClinicRepository(":memory:")
    yield ClinicService(repository, notifier)
    repository.close()
