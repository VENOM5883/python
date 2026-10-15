def test_list(client):
    data = client.get("/appointments").json()
    assert data["total"] == 8 and len(data["items"]) == 8


def test_get_existing(client):
    response = client.get("/appointments/1")
    assert response.status_code == 200 and response.json()["patient"] == "Иванов Иван Иванович"


def test_get_missing(client):
    assert client.get("/appointments/999").status_code == 404


def test_create(client, payload):
    response = client.post("/appointments", json=payload)
    assert response.status_code == 201 and response.json()["status"] == "planned"


def test_create_invalid(client, payload):
    assert client.post("/appointments", json={**payload, "cabinet": -5}).status_code == 422


def test_validation_error_missing_field(client, payload):
    payload.pop("doctor")
    response = client.post("/appointments", json=payload)
    assert response.status_code == 422 and response.json()["detail"][0]["loc"][-1] == "doctor"


def test_conflict(client, payload):
    client.post("/appointments", json=payload)
    assert client.post("/appointments", json={**payload, "patient": "Другой"}).status_code == 409


def test_put(client, payload):
    response = client.put("/appointments/2", json={**payload, "status": "confirmed"})
    assert response.status_code == 200 and response.json()["doctor"] == "Белова М.И."


def test_patch(client):
    response = client.patch("/appointments/4", json={"status": "confirmed"})
    assert response.json()["status"] == "confirmed" and response.json()["doctor"] == "Орлова Н.А."
    assert client.patch("/appointments/4", json={}).status_code == 400


def test_delete_twice(client):
    assert client.delete("/appointments/5").status_code == 204
    assert client.delete("/appointments/5").status_code == 404


def test_filter(client):
    data = client.get("/appointments", params={"specialty": "кардиолог", "status": "completed"}).json()
    assert [a["id"] for a in data["items"]] == [3]


def test_sort(client):
    items = client.get("/appointments", params={"sort": "cabinet", "order": "desc"}).json()["items"]
    assert items[0]["cabinet"] == 310
    assert client.get("/appointments", params={"sort": "salary"}).status_code == 400


def test_pagination(client):
    data = client.get("/appointments", params={"skip": 6, "limit": 5}).json()
    assert data["total"] == 8 and len(data["items"]) == 2


def test_search(client):
    data = client.get("/appointments/search", params={"q": "Кузнецов"}).json()
    assert len(data) == 3 and all(a["doctor"] == "Кузнецов О.П." for a in data)


def test_statistics(client):
    data = client.get("/appointments/statistics").json()
    assert data["total"] == 8 and data["by_status"]["completed"] == 2
    assert data["busiest_doctor"] == "Кузнецов О.П."


def test_cache_miss_hit_and_invalidation(client):
    assert client.get("/appointments/6").headers["X-Cache"] == "MISS"
    assert client.get("/appointments/6").headers["X-Cache"] == "HIT"
    client.patch("/appointments/6", json={"cabinet": 121})
    response = client.get("/appointments/6")
    assert response.headers["X-Cache"] == "MISS" and response.json()["cabinet"] == 121


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}
