def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}


def test_register_login_profile(client, user):
    profile = client.get("/auth/profile", headers=user).json()
    assert profile["role"] == "USER" and profile["full_name"] == "Семик Алексей"


def test_register_conflicts_and_bad_login(client, user):
    data = {"email": "user@test.ru", "password": "password123", "full_name": "X Y", "phone": "+79009999999"}
    assert client.post("/auth/register", json=data).json()["error"] == "EMAIL_TAKEN"
    assert client.post("/auth/login", json={"email": "user@test.ru", "password": "bad"}).status_code == 401


def test_unauthorized_and_forbidden(client, user):
    assert client.get("/orders").status_code == 401
    assert client.get("/orders", headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert client.post("/products", headers=user, json={}).status_code == 403
    assert client.get("/warehouses", headers=user).status_code == 403


def test_catalog_search_filter_sort_pagination(client):
    data = client.get("/products", params={"category": "обезболивающие", "sort": "price", "order": "desc"}).json()
    assert [p["name"] for p in data["items"]] == ["Ибупрофен", "Парацетамол"]
    assert data["items"][1]["available"] == 100
    assert client.get("/products", params={"q": "Озон"}).json()["total"] == 2
    page = client.get("/products", params={"skip": 4, "limit": 4}).json()
    assert page["total"] == 6 and len(page["items"]) == 2
    assert client.get("/products", params={"sort": "secret"}).status_code == 400


def test_admin_product_crud(client, admin):
    created = client.post("/products", headers=admin, json={"name": "Аспирин", "category": "обезболивающие",
                                                            "manufacturer": "Bayer", "price": "99.50"})
    assert created.status_code == 201
    product_id = created.json()["id"]
    assert client.patch(f"/products/{product_id}", headers=admin, json={"price": "105"}).json()["price"] == "105.00"
    assert client.post("/products", headers=admin, json={"name": "Аспирин", "category": "xx", "manufacturer": "yy",
                                                         "price": 1}).status_code == 409
    assert client.delete(f"/products/{product_id}", headers=admin).status_code == 204
    assert client.get(f"/products/{product_id}").json()["error"] == "PRODUCT_NOT_FOUND"


def test_order_lifecycle_with_stock_control(client, admin, user):
    order = client.post("/orders", headers=user, json={"items": [{"product_id": 5, "quantity": 30}]})
    assert order.status_code == 201
    body = order.json()
    assert [(i["warehouse_id"], i["quantity"]) for i in body["items"]] == [(1, 25), (2, 5)]
    assert client.get("/products/5").json()["available"] == 20
    assert client.patch(f"/orders/{body['id']}/status", headers=user, json={"status": "completed"}).status_code == 403
    assert client.patch(f"/orders/{body['id']}/status", headers=user, json={"status": "cancelled"}).status_code == 200
    assert client.get("/products/5").json()["available"] == 50
    assert client.patch(f"/orders/{body['id']}/status", headers=user, json={"status": "paid"}).status_code == 409


def test_order_business_rules(client, user):
    assert client.post("/orders", headers=user, json={"items": [{"product_id": 6, "quantity": 1}]}).json()["error"] \
        == "OUT_OF_STOCK"
    assert client.post("/orders", headers=user, json={"items": [{"product_id": 3, "quantity": 1}]}).json()["error"] \
        == "PRESCRIPTION_REQUIRED"
    assert client.post("/orders", headers=user, json={"has_prescription": True,
                                                      "items": [{"product_id": 3, "quantity": 1}]}).status_code == 201
    assert client.post("/orders", headers=user, json={"items": [{"product_id": 1, "quantity": 0}]}).status_code == 422


def test_users_see_only_own_orders(client, admin, make_user):
    alice, bob = make_user("alice@test.ru", "+79000000001"), make_user("bob@test.ru", "+79000000002")
    order_id = client.post("/orders", headers=alice, json={"items": [{"product_id": 2, "quantity": 1}]}).json()["id"]
    assert client.get(f"/orders/{order_id}", headers=bob).status_code == 403
    assert client.get("/orders", headers=bob).json() == []
    assert len(client.get("/orders", headers=admin).json()) == 1


def test_loyalty_discount_and_statistics(client, admin, user):
    order = client.post("/orders", headers=user, json={"items": [{"product_id": 4, "quantity": 17}]}).json()
    client.patch(f"/orders/{order['id']}/status", headers=user, json={"status": "paid"})
    client.patch(f"/orders/{order['id']}/status", headers=admin, json={"status": "completed"})
    second = client.post("/orders", headers=user, json={"items": [{"product_id": 2, "quantity": 10}]}).json()
    assert second["discount"] == "44.50" and second["total"] == "845.50"
    stats = client.get("/orders/statistics", headers=admin).json()
    assert stats["completed"] == 1 and stats["revenue"] == 5270.0


def test_cannot_delete_ordered_product(client, admin, user):
    client.post("/orders", headers=user, json={"items": [{"product_id": 5, "quantity": 1}]})
    assert client.delete("/products/5", headers=admin).json()["error"] == "PRODUCT_IN_ORDERS"


def test_warehouse_and_stock_management(client, admin):
    warehouse = client.post("/warehouses", headers=admin, json={"name": "Склад №3", "address": "г. Химки, ул. Мира, 5",
                                                                "priority": 3}).json()
    assert client.put("/warehouses/stock", headers=admin, json={"product_id": 6, "warehouse_id": warehouse["id"],
                                                                "quantity": 15}).status_code == 200
    assert client.get("/products/6").json()["available"] == 15
    assert client.put("/warehouses/stock", headers=admin, json={"product_id": 6, "warehouse_id": 999,
                                                                "quantity": 1}).status_code == 404
