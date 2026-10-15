def test_cache_aside(service, new_data):
    created = service.add(new_data)
    service.get(created["_id"])
    assert service.last_source.startswith("MongoDB")
    service.get(created["_id"])
    assert service.last_source.startswith("Redis")


def test_invalidation(service, new_data):
    created = service.add(new_data)
    service.get(created["_id"])
    service.update(created["_id"], {"status": "confirmed"})
    document = service.get(created["_id"])
    assert service.last_source.startswith("MongoDB") and document["status"] == "confirmed"


def test_schedule_cache_invalidated_on_change(service, new_data):
    _, source = service.doctor_schedule(1, "2026-10-25")
    assert source == "MongoDB"
    assert service.doctor_schedule(1, "2026-10-25")[1] == "Redis"
    service.add(new_data)
    slots, source = service.doctor_schedule(1, "2026-10-25")
    assert source == "MongoDB" and len(slots) == 1
