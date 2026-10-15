def test_redis_write_read_types(service):
    cache = service.cache
    cache.set_doctor({"id": 9, "full_name": "Врач", "specialty": "хирург", "cabinet": 1})  # Hash
    assert cache.get_doctor(9)["specialty"] == "хирург"
    cache.set_schedule(9, "2026-10-25", ["09:00", "09:30"])                               # List
    assert cache.get_schedule(9, "2026-10-25") == ["09:00", "09:30"]
    cache.log_query("иванов")
    assert cache.recent_queries() == ["иванов"]


def test_sorted_set_nearest(service, new_data):
    created = service.add({**new_data, "date": "2026-10-19"})
    assert service.cache.nearest(1)[0][0] == created["_id"]


def test_ttl(service, new_data):
    created = service.add(new_data)
    service.get(created["_id"])
    assert 0 < service.cache.ttl(f"appointment:{created['_id']}") <= 120
