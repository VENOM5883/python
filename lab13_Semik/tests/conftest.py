import sys
from pathlib import Path

import fakeredis
import mongomock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cache import RedisCache  # noqa: E402
from app.repository import MongoRepository  # noqa: E402
from app.seed import DOCTORS, generate  # noqa: E402
from app.service import ClinicService  # noqa: E402


@pytest.fixture
def repository():
    repository = MongoRepository(mongomock.MongoClient()["clinic_test"])
    repository.insert_many(generate())
    repository.create_indexes()
    return repository


@pytest.fixture
def service(repository):
    return ClinicService(repository, RedisCache(fakeredis.FakeRedis(decode_responses=True)))


@pytest.fixture
def new_data():
    return {"patient": {"full_name": "Тестов Тест", "birth_year": 1990, "phone": "+7"},
            "doctor": dict(DOCTORS[0]), "specialty": "терапевт", "date": "2026-10-25", "time": "15:00"}
