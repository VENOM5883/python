import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"   # БД в памяти для тестов
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.cache import cache  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    cache.redis.flushdb()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def payload():
    return {"patient": "Тестов Тест", "doctor": "Белова М.И.", "specialty": "окулист",
            "date": "2026-10-25", "time": "10:00:00", "cabinet": 120}
