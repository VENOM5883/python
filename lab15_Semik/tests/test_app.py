import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402


class TestConfig(Config):
    DATABASE_URL = "sqlite://"
    SECRET_KEY = "test"


@pytest.fixture
def client():
    app = create_app(TestConfig)
    app.config["TESTING"] = True
    return app.test_client()


def test_pages(client):
    for url in ("/", "/medicines", "/medicines/1", "/medicines/create", "/medicines/1/edit",
                "/categories/1", "/purchases"):
        assert client.get(url).status_code == 200, url


def test_404_page(client):
    response = client.get("/medicines/999")
    assert response.status_code == 404 and "404" in response.get_data(as_text=True)


def test_search_filter_sort(client):
    html = client.get("/medicines?search=Озон&sort=-price").get_data(as_text=True)
    assert html.index("Омепразол") < html.index("Лоратадин") and "Парацетамол" not in html
    html = client.get("/medicines?category=2&in_stock=on").get_data(as_text=True)
    assert "Амоксициллин" in html and "Азитромицин" not in html
    html = client.get("/medicines?prescription=yes").get_data(as_text=True)
    assert "Ибупрофен" not in html


def test_create_edit_delete_via_forms(client):
    form = {"name": "Но-шпа", "manufacturer": "Sanofi", "form": "таблетки", "price": "150",
            "quantity": "10", "category_id": "1"}
    response = client.post("/medicines/create", data=form, follow_redirects=True)
    assert "Препарат добавлен" in response.get_data(as_text=True)
    assert client.post("/medicines/create", data=form).status_code == 409
    response = client.post("/medicines/11/edit", data={**form, "price": "175"}, follow_redirects=True)
    assert "175.00" in response.get_data(as_text=True)
    response = client.post("/medicines/11/delete", follow_redirects=True)
    assert "Препарат удалён" in response.get_data(as_text=True)


def test_purchase_and_protection(client):
    response = client.post("/purchases", data={"customer_name": "Иванов", "qty_1": "2", "qty_8": "1"},
                           follow_redirects=True)
    assert "на сумму 185.00 руб." in response.get_data(as_text=True)
    response = client.post("/purchases", data={"customer_name": "Иванов", "qty_3": "999"},
                           follow_redirects=True)
    assert "Недостаточно" in response.get_data(as_text=True)
    response = client.post("/medicines/1/delete", follow_redirects=True)
    assert "удалить нельзя" in response.get_data(as_text=True)


def test_rest_api(client):
    assert len(client.get("/api/medicines").get_json()) == 10
    created = client.post("/api/medicines", json={"name": "Аспирин", "manufacturer": "Bayer", "form": "таблетки",
                                                  "price": 99, "quantity": 5, "category_id": 1})
    assert created.status_code == 201
    medicine_id = created.get_json()["id"]
    assert client.patch(f"/api/medicines/{medicine_id}", json={"price": 105}).get_json()["price"] == 105
    assert client.post("/api/medicines", json={"name": "X"}).status_code == 400
    assert client.delete(f"/api/medicines/{medicine_id}").status_code == 204
    assert client.get(f"/api/medicines/{medicine_id}").status_code == 404
    assert client.post("/api/purchases", json={"customer_name": "Петров", "items": {"2": 1}}).status_code == 201
