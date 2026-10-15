import pytest

from exceptions import ConflictError, NotFoundError, ValidationError

NEW = {"doctor_id": 4, "date": "2026-10-25", "time": "10:00"}


def test_repository_get_all(service):
    assert len(service.repository.get_all()) == 12


def test_create_read(client):
    created = client.post("/appointments", json=NEW)
    assert created.status_code == 201
    response = client.get(f"/appointments/{created.get_json()['id']}")
    assert response.get_json()["doctor"] == "Белова Мария Игоревна"


def test_update_patch_and_put(client):
    patched = client.patch("/appointments/3", json={"patient_id": 4}).get_json()
    assert patched["status"] == "booked" and patched["patient"] == "Новикова Ольга Дмитриевна"
    put = client.put("/appointments/3", json={"doctor_id": 1, "date": "2026-10-20", "time": "10:00"})
    assert put.get_json()["status"] == "free"


def test_delete(client):
    assert client.delete("/appointments/9").status_code == 204
    assert client.get("/appointments/9").status_code == 404


def test_not_found_error(service):
    with pytest.raises(NotFoundError):
        service.get(999)


def test_validation(client):
    assert client.post("/appointments", json={"doctor_id": 1}).status_code == 400
    assert client.post("/appointments", json={**NEW, "doctor_id": 77}).status_code == 400
    assert client.post("/appointments", json={**NEW, "time": "25:99"}).status_code == 400


def test_unique_slot_conflict(service):
    with pytest.raises(ConflictError):
        service.create({"doctor_id": 1, "date": "2026-10-20", "time": "09:00"})


def test_transaction_commit(service):
    result = service.complete(2, [{"service_id": 2, "quantity": 1}, {"service_id": 3}])
    assert result["status"] == "completed"
    assert result["total_cost"] == 1500 + 1200 + 800  # услуга №1 добавлена в seed


def test_transaction_rollback(service):
    with pytest.raises(ConflictError):
        service.complete(10, [{"service_id": 1}, {"service_id": 999}])  # нет такой услуги
    assert service.get(10)["status"] == "booked"  # статус откатился
    assert service.repository.db.execute(
        "SELECT COUNT(*) FROM appointment_services WHERE appointment_id = 10").fetchone()[0] == 0


def test_free_appointments_special_query(client):
    data = client.get("/appointments/free?specialty=терапевт").get_json()
    assert {a["id"] for a in data} == {3, 11}


def test_filter_and_sort(client):
    data = client.get("/appointments?status=booked&sort=datetime&order=desc").get_json()
    assert [a["id"] for a in data] == [12, 10, 6, 2]
    assert client.get("/appointments?sort=password").status_code == 400


def test_sql_injection_is_harmless(client):
    data = client.get("/appointments?specialty=' OR '1'='1").get_json()
    assert data == []


def test_redis_cache_aside_and_invalidation(service):
    assert service.schedule(1, "2026-10-20")["source"] == "database"
    cached = service.schedule(1, "2026-10-20")
    assert cached["source"] == "redis" and 0 < cached["ttl"] <= 60
    service.update(3, {"patient_id": 2}, partial=True)
    assert service.schedule(1, "2026-10-20")["source"] == "database"
    assert service.cache.views(1) == 3


def test_validation_error_type(service):
    with pytest.raises(ValidationError):
        service.update(1, {}, partial=True)
