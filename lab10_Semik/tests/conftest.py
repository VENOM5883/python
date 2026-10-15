import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


@pytest.fixture
def client():
    return create_app().test_client()


@pytest.fixture
def new_slot():
    return {"doctor": "Белова М.И.", "specialty": "окулист", "date": "2026-10-22",
            "time": "14:00", "cabinet": 120}
