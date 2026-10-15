import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(create_app("sqlite://"))


def auth_header(client, email, password):
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin(client):
    return auth_header(client, settings.admin_email, settings.admin_password)


@pytest.fixture
def make_user(client):
    def factory(email="user@test.ru", phone="+79001234567"):
        client.post("/auth/register", json={"email": email, "password": "password123",
                                            "full_name": "Семик Алексей", "phone": phone})
        return auth_header(client, email, "password123")
    return factory


@pytest.fixture
def user(make_user):
    return make_user()
