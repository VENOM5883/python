from repository import AppointmentRepository

DATA = {"doctor": "Д", "specialty": "терапевт", "date": "2026-10-20", "time": "09:00", "cabinet": 1}


def test_create_and_get():
    repo = AppointmentRepository()
    created = repo.create(DATA)
    assert repo.get_by_id(created.id) == created


def test_delete_returns_flag():
    repo = AppointmentRepository()
    created = repo.create(DATA)
    assert repo.delete(created.id) is True
    assert repo.delete(created.id) is False
