import sys
from pathlib import Path

import fakeredis
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from cache import ScheduleCache  # noqa: E402
from database import connect, init_db  # noqa: E402
from repository import AppointmentRepository  # noqa: E402
from service import AppointmentService  # noqa: E402


@pytest.fixture
def client(tmp_path):
    return create_app(str(tmp_path / "test.db"), fakeredis.FakeRedis(decode_responses=True)).test_client()


@pytest.fixture
def service():
    connection = connect(":memory:")
    init_db(connection)
    return AppointmentService(AppointmentRepository(connection),
                              ScheduleCache(fakeredis.FakeRedis(decode_responses=True)))
