import pytest

from app.service import NotFoundError


def test_connection_and_seed(repository):
    assert repository.count() == 24
    assert {"doctor_date_time", "status_specialty"} <= set(repository.collection.index_information())


def test_add_and_get_document(service, new_data):
    created = service.add(new_data)
    assert service.repository.get(created["_id"])["patient"]["full_name"] == "Тестов Тест"


def test_update_document(service, new_data):
    created = service.add(new_data)
    service.repository.add_prescription(created["_id"], "Витамин C")
    updated = service.update(created["_id"], {"status": "completed", "diagnosis": "Здоров"})
    assert updated["status"] == "completed" and updated["prescriptions"] == ["Витамин C"]


def test_delete_document(service, new_data):
    created = service.add(new_data)
    service.delete(created["_id"])
    with pytest.raises(NotFoundError):
        service.get(created["_id"])


def test_filters_nested_and_array(repository):
    assert all(d["status"] == "planned" for d in repository.by_status("planned"))
    assert all("Петрова" in d["patient"]["full_name"] for d in repository.by_patient_name("петрова"))
    assert len(repository.upcoming("2026-10-21", limit=5)) == 5
    for document in repository.by_prescription("Парацетамол"):
        assert "Парацетамол" in document["prescriptions"]


def test_aggregation(repository):
    by_status = {r["_id"]: r["count"] for r in repository.count_by_status()}
    assert sum(by_status.values()) == 24
    workload = repository.doctors_workload()
    assert workload[0]["appointments"] >= workload[-1]["appointments"]


def test_invalid_id_and_data(service, new_data):
    with pytest.raises(ValueError):
        service.get("not-an-object-id")
    with pytest.raises(ValueError):
        service.add({**new_data, "status": "lost"})
