import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from common.broker import InMemoryBroker


@pytest.fixture
def broker():
    return InMemoryBroker()


@pytest.fixture
def client(broker):
    return TestClient(create_app("sqlite://", broker))


def reserve(client, order_id, items):
    return client.post("/reservations", json={"order_id": order_id, "items": items})


def test_stock_list_and_get(client):
    assert len(client.get("/stock").json()) == 5
    assert client.get("/stock/1").json()["available"] == 100
    assert client.get("/stock/42").status_code == 404


def test_reserve_reduces_available(client, broker):
    assert reserve(client, "o1", [{"product_id": 1, "quantity": 10}]).status_code == 201
    assert client.get("/stock/1").json() == {"product_id": 1, "quantity": 100, "reserved": 10, "available": 90}
    assert broker.events[-1]["type"] == "ProductReserved"


def test_reserve_is_atomic(client):
    response = reserve(client, "o2", [{"product_id": 1, "quantity": 5}, {"product_id": 5, "quantity": 1}])
    assert response.status_code == 409
    assert client.get("/stock/1").json()["reserved"] == 0  # первая позиция не зарезервирована


def test_duplicate_reservation(client):
    reserve(client, "o3", [{"product_id": 2, "quantity": 1}])
    assert reserve(client, "o3", [{"product_id": 2, "quantity": 1}]).status_code == 409


def test_release_compensation(client):
    reserve(client, "o4", [{"product_id": 3, "quantity": 4}])
    assert client.delete("/reservations/o4").json()["released_items"] == 1
    assert client.get("/stock/3").json()["reserved"] == 0
    assert client.delete("/reservations/o4").status_code == 404


def test_receive_stock_publishes_event(client, broker):
    assert client.put("/stock/5", json={"quantity": 30}).json()["available"] == 30
    assert broker.events[-1]["type"] == "StockReceived" and broker.events[-1]["payload"]["received"] == 30


def test_cannot_set_below_reserved_or_delete_reserved(client):
    reserve(client, "o5", [{"product_id": 4, "quantity": 20}])
    assert client.put("/stock/4", json={"quantity": 10}).status_code == 409
    assert client.delete("/stock/4").status_code == 409


def test_validation(client):
    assert reserve(client, "o6", [{"product_id": 1, "quantity": 0}]).status_code == 422
    assert reserve(client, "o6", []).status_code == 422
