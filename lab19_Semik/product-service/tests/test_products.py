import pytest
from fastapi.testclient import TestClient

from app.main import Product, ProductService, create_app


@pytest.fixture
def client():
    return TestClient(create_app("sqlite://"))


NEW = {"name": "Аспирин", "manufacturer": "Bayer", "category": "обезболивающие", "price": "120.50"}


def test_list_seeded(client):
    assert len(client.get("/products").json()) == 5


def test_filter_by_category(client):
    names = [p["name"] for p in client.get("/products", params={"category": "обезболивающие"}).json()]
    assert names == ["Парацетамол", "Ибупрофен"]


def test_get_and_404(client):
    assert client.get("/products/3").json()["prescription_required"] is True
    assert client.get("/products/99").status_code == 404


def test_create(client):
    response = client.post("/products", json=NEW)
    assert response.status_code == 201 and response.json()["price"] == "120.50"


def test_validation(client):
    assert client.post("/products", json={**NEW, "price": -1}).status_code == 422
    assert client.post("/products", json={"name": "A"}).status_code == 422


def test_duplicate_conflict(client):
    client.post("/products", json=NEW)
    assert client.post("/products", json=NEW).status_code == 409


def test_update_and_delete(client):
    assert client.put("/products/1", json={**NEW, "name": "Парацетамол 500"}).json()["name"] == "Парацетамол 500"
    assert client.delete("/products/1").status_code == 204
    assert client.get("/products/1").status_code == 404


def test_service_layer_unit():
    from unittest.mock import MagicMock
    session = MagicMock()
    session.get.return_value = None
    with pytest.raises(Exception) as error:
        ProductService(session).get(1)
    assert error.value.status_code == 404
    session.get.assert_called_once_with(Product, 1)


def test_health(client):
    assert client.get("/health").json()["status"] == "healthy"
