import json
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from common.broker import InMemoryBroker
from common.resilience import CircuitBreaker, ResilientClient

PRODUCTS = {1: {"id": 1, "name": "Парацетамол", "price": "45.00", "prescription_required": False},
            3: {"id": 3, "name": "Амоксициллин", "price": "210.00", "prescription_required": True}}


class FakeServices:
    """Имитация product-service и warehouse-service через httpx.MockTransport."""

    def __init__(self):
        self.reserved, self.released = {}, []
        self.warehouse_down = False
        self.calls = Mock()

    def product_handler(self, request: httpx.Request) -> httpx.Response:
        product_id = int(request.url.path.rsplit("/", 1)[-1])
        return httpx.Response(200, json=PRODUCTS[product_id]) if product_id in PRODUCTS \
            else httpx.Response(404, json={"detail": "not found"})

    def warehouse_handler(self, request: httpx.Request) -> httpx.Response:
        self.calls(request.method, request.url.path)
        if self.warehouse_down:
            raise httpx.ConnectError("connection refused", request=request)
        if request.method == "POST":
            body = json.loads(request.content)
            if any(i["quantity"] > 10 for i in body["items"]):
                return httpx.Response(409, json={"detail": "Not enough product"})
            self.reserved[body["order_id"]] = body["items"]
            return httpx.Response(201, json={"order_id": body["order_id"]})
        self.released.append(request.url.path.rsplit("/", 1)[-1])
        return httpx.Response(200, json={"released_items": 1})


@pytest.fixture
def fake():
    return FakeServices()


@pytest.fixture
def broker():
    return InMemoryBroker()


@pytest.fixture
def client(fake, broker):
    products = ResilientClient("product-service", "http://products", transport=httpx.MockTransport(fake.product_handler))
    warehouse = ResilientClient("warehouse-service", "http://warehouse", attempts=2,
                                breaker=CircuitBreaker("warehouse-service", failure_threshold=2, reset_timeout=60),
                                transport=httpx.MockTransport(fake.warehouse_handler))
    return TestClient(create_app("sqlite://", products, warehouse, broker))


ORDER = {"customer": "Семик А.", "items": [{"product_id": 1, "quantity": 2}]}


def test_create_order_interaction(client, fake, broker):
    response = client.post("/orders", json=ORDER)
    assert response.status_code == 201 and response.json()["total"] == 90.0
    assert fake.reserved[response.json()["id"]] == [{"product_id": 1, "quantity": 2}]
    assert broker.events[-1]["type"] == "OrderCreated"


def test_get_and_list(client):
    order_id = client.post("/orders", json=ORDER).json()["id"]
    assert client.get(f"/orders/{order_id}").json()["customer"] == "Семик А."
    assert len(client.get("/orders").json()) == 1
    assert client.get("/orders/unknown").status_code == 404


def test_unknown_product(client):
    assert client.post("/orders", json={"customer": "Х Х", "items": [{"product_id": 77, "quantity": 1}]}).status_code == 400


def test_prescription_required(client, fake):
    response = client.post("/orders", json={"customer": "Х Х", "items": [{"product_id": 3, "quantity": 1}]})
    assert response.status_code == 400 and fake.reserved == {}
    assert client.post("/orders", json={"customer": "Х Х", "has_prescription": True,
                                        "items": [{"product_id": 3, "quantity": 1}]}).status_code == 201


def test_not_enough_stock(client, broker):
    response = client.post("/orders", json={"customer": "Х Х", "items": [{"product_id": 1, "quantity": 50}]})
    assert response.status_code == 409 and broker.events == []


def test_cancel_releases_reservation(client, fake, broker):
    order_id = client.post("/orders", json=ORDER).json()["id"]
    assert client.put(f"/orders/{order_id}", json={"status": "cancelled"}).json()["status"] == "cancelled"
    assert fake.released == [order_id] and broker.events[-1]["type"] == "OrderCancelled"
    assert client.put(f"/orders/{order_id}", json={"status": "completed"}).status_code == 409
    assert client.delete(f"/orders/{order_id}").status_code == 204


def test_delete_active_order_forbidden(client):
    order_id = client.post("/orders", json=ORDER).json()["id"]
    assert client.delete(f"/orders/{order_id}").status_code == 409


def test_warehouse_unavailable_retry_and_circuit_breaker(client, fake):
    fake.warehouse_down = True
    assert client.post("/orders", json=ORDER).status_code == 503
    assert fake.calls.call_count == 2                     # Retry: 2 попытки
    assert client.post("/orders", json=ORDER).status_code == 503
    assert client.get("/health").json()["circuit_breakers"][1]["state"] == "OPEN"
    calls = fake.calls.call_count
    assert client.post("/orders", json=ORDER).status_code == 503
    assert fake.calls.call_count == calls                 # при OPEN запрос к складу не отправляется


def test_validation(client):
    assert client.post("/orders", json={"customer": "А", "items": []}).status_code == 422
