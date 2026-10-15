import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from aiogram.fsm.storage.memory import MemoryStorage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot import build_dispatcher  # noqa: E402
from database.db import connect, init_db  # noqa: E402
from database.repository import ClinicRepository  # noqa: E402
from services.clinic_service import ClinicService  # noqa: E402
from simulator import TelegramSimulator  # noqa: E402

ADMIN_ID, USER_ID = 1, 2


@pytest.fixture
def service():
    connection = connect(":memory:")
    init_db(connection)
    return ClinicService(ClinicRepository(connection))


@pytest.fixture
def future_day():
    day = date.today() + timedelta(days=7)
    while day.weekday() == 6:
        day += timedelta(days=1)
    return day


_dispatcher = None


@pytest.fixture
def make_sim(service):
    """Routers aiogram подключаются к одному Dispatcher, поэтому он создаётся один раз,
    а для каждого теста подменяются сервис (чистая БД) и хранилище FSM."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = build_dispatcher(service, frozenset({ADMIN_ID}))
    _dispatcher["service"] = service
    _dispatcher.fsm.storage = MemoryStorage()

    def factory(user_id=USER_ID):
        return TelegramSimulator(_dispatcher, user_id=user_id)
    return factory
