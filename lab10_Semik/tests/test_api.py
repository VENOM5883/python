def test_get_list(client):
    response = client.get("/appointments")
    assert response.status_code == 200
    assert len(response.get_json()) == 6


def test_get_one(client):
    response = client.get("/appointments/1")
    assert response.status_code == 200
    assert response.get_json()["patient"] == "Иванов И.И."


def test_create(client, new_slot):
    response = client.post("/appointments", json=new_slot)
    assert response.status_code == 201
    assert response.get_json()["status"] == "free"
    assert response.headers["Location"].endswith(str(response.get_json()["id"]))


def test_put(client, new_slot):
    response = client.put("/appointments/2", json={**new_slot, "patient": "Сидоров"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "booked"


def test_404(client):
    response = client.get("/appointments/999")
    assert response.status_code == 404
    assert response.get_json()["code"] == "APPOINTMENT_NOT_FOUND"


def test_400_invalid_body_and_id(client):
    assert client.post("/appointments", json={"doctor": ""}).status_code == 400
    assert client.get("/appointments/abc").status_code == 400
    assert client.post("/appointments", data="not json").status_code == 400


def test_patch(client):
    response = client.patch("/appointments/3", json={"patient": "Новиков"})
    assert response.status_code == 200
    assert response.get_json()["doctor"] == "Смирнова Е.В."
    assert response.get_json()["status"] == "booked"


def test_delete(client):
    assert client.delete("/appointments/6").status_code == 204
    assert client.delete("/appointments/6").status_code == 404


def test_filter_and_sort(client):
    data = client.get("/appointments?specialty=кардиолог&status=free").get_json()
    assert [a["id"] for a in data] == [5]
    data = client.get("/appointments?sort=cabinet&order=desc").get_json()
    assert data[0]["cabinet"] == 310
    assert client.get("/appointments?sort=salary").status_code == 400


def test_free_endpoint(client):
    data = client.get("/appointments/free").get_json()
    assert {a["id"] for a in data} == {2, 3, 5, 6}
    assert all(a["status"] == "free" for a in data)


def test_method_not_allowed(client):
    response = client.delete("/appointments")
    assert response.status_code == 405
    assert response.get_json()["code"] == "METHOD_NOT_ALLOWED"
