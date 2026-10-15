import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app("sqlite://"))


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy", "database": True, "version": "1.0.0"}


def test_crud(client):
    created = client.post("/medicines", json={"name": "Аспирин", "category": "обезболивающие",
                                              "price": "99.90", "quantity": 5})
    assert created.status_code == 201
    medicine_id = created.json()["id"]
    assert client.get(f"/medicines/{medicine_id}").json()["name"] == "Аспирин"
    assert client.put(f"/medicines/{medicine_id}", json={"name": "Аспирин", "category": "обезболивающие",
                                                         "price": "105", "quantity": 5}).json()["price"] in ("105", "105.00")
    assert client.delete(f"/medicines/{medicine_id}").status_code == 204
    assert client.get(f"/medicines/{medicine_id}").status_code == 404


def test_filter_and_validation(client):
    assert len(client.get("/medicines", params={"category": "обезболивающие"}).json()) == 2
    assert client.post("/medicines", json={"name": "X", "category": "y", "price": 0, "quantity": -1}).status_code == 422
    assert client.post("/medicines", json={"name": "Парацетамол", "category": "обезболивающие",
                                           "price": 1, "quantity": 1}).status_code == 409


def test_sale_flow(client):
    assert client.post("/sales", json={"medicine_id": 4, "quantity": 2}).json()["total"] == "620.00"
    assert client.get("/medicines/4").json()["quantity"] == 33
    assert client.post("/sales", json={"medicine_id": 4, "quantity": 100}).status_code == 409
    assert client.delete("/medicines/4").status_code == 409


def test_data_persists_in_file_database(tmp_path):
    url = f"sqlite:///{tmp_path / 'p.db'}"
    TestClient(create_app(url)).post("/sales", json={"medicine_id": 1, "quantity": 20})
    assert TestClient(create_app(url)).get("/medicines/1").json()["quantity"] == 100  # «перезапуск контейнера»
