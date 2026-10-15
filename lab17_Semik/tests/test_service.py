import pytest

from services.clinic_service import ClinicError, validate_date, validate_name, validate_phone


@pytest.mark.parametrize("value, ok", [("Иванов Иван", True), ("Иван", False), ("123 456", False)])
def test_validate_name(value, ok):
    if ok:
        assert validate_name(value) == value
    else:
        with pytest.raises(ClinicError):
            validate_name(value)


def test_validate_phone_normalizes():
    assert validate_phone("8 (900) 123-45-67") == "+79001234567"
    with pytest.raises(ClinicError):
        validate_phone("12345")


def test_validate_date(future_day):
    assert validate_date(future_day.strftime("%d.%m.%Y")) == future_day.isoformat()
    for bad in ("31.02.2026", "01.01.2000", "abc"):
        with pytest.raises(ClinicError):
            validate_date(bad)


async def test_register_and_book_create_read(service, future_day):
    await service.register(50, "Семик Алексей", "+79001234567")
    appointment = await service.book(50, 3, future_day.isoformat(), "10:00", "Давление")
    assert appointment["doctor"] == "Кузнецов Олег Петрович"
    assert [a["id"] for a in await service.my_appointments(50)] == [appointment["id"]]


async def test_time_slot_cannot_be_double_booked(service, future_day):
    await service.register(50, "Семик Алексей", "+79001234567")
    await service.register(51, "Петров Пётр", "+79007654321")
    await service.book(50, 1, future_day.isoformat(), "15:30", "Кашель")
    assert "15:30" not in await service.free_times(1, future_day.isoformat())
    with pytest.raises(ClinicError):
        await service.book(51, 1, future_day.isoformat(), "15:30", "Кашель")


async def test_update_cancel_delete(service, future_day):
    await service.register(50, "Семик Алексей", "+79001234567")
    appointment = await service.book(50, 2, future_day.isoformat(), "11:00", "Слабость")
    updated = await service.change_complaint(50, appointment["id"], "Слабость и кашель")
    assert updated["complaint"] == "Слабость и кашель"
    with pytest.raises(ClinicError):
        await service.delete(50, appointment["id"])  # сначала нужно отменить
    await service.cancel(50, appointment["id"])
    await service.delete(50, appointment["id"])
    assert await service.history(50) == []


async def test_foreign_appointment_is_hidden(service):
    await service.register(50, "Семик Алексей", "+79001234567")
    with pytest.raises(ClinicError):
        await service.appointment(50, 1)  # запись другого пациента


async def test_search(service):
    assert [d["full_name"] for d in await service.search_doctors("окул")] == ["Белова Мария Игоревна"]
    with pytest.raises(ClinicError):
        await service.search_doctors("a")
