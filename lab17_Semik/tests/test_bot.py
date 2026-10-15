from conftest import ADMIN_ID


async def register(sim):
    await sim.send("/start")
    await sim.send("Семик Алексей")
    return await sim.send("+79001234567")


async def test_start_registration_and_validation(make_sim):
    sim = make_sim()
    assert "зарегистрируйтесь" in (await sim.send("/start"))[0]
    assert "буквами" in (await sim.send("42"))[0]
    await sim.send("Семик Алексей")
    assert "формате" in (await sim.send("телефон"))[0]
    assert "Регистрация завершена" in (await sim.send("+79001234567"))[0]


async def test_fsm_booking_scenario(make_sim, future_day, service):
    sim = make_sim()
    await register(sim)
    await sim.send("/book")
    await sim.press("Терапевт")
    await sim.press("Смирнова")
    assert "прошедшую" in (await sim.send("01.01.2020"))[0]
    assert (await sim.send(future_day.strftime("%d.%m.%Y")))[0] == "Выберите время:"
    await sim.press("12:00")
    assert "подробнее" in (await sim.send("а"))[0]
    await sim.send("Кашель и насморк")
    assert "Вы записаны" in (await sim.press("✅"))[0]
    assert len(await service.my_appointments(sim.user.id)) == 1


async def test_cancel_command_resets_fsm(make_sim):
    sim = make_sim()
    await register(sim)
    await sim.send("/book")
    assert (await sim.send("/cancel"))[0] == "Действие отменено."
    assert "кнопки" not in (await sim.send("текст"))[0]


async def test_stale_button_and_buttons_only_state(make_sim):
    sim = make_sim()
    await register(sim)
    await sim.send("/book")
    assert "кнопки" in (await sim.send("кардиолог"))[0]


async def test_admin_rights(make_sim):
    user, admin = make_sim(), make_sim(ADMIN_ID)
    assert "только администратору" in (await user.send("/stats"))[0]
    assert "appointments: 9" in (await admin.send("/stats"))[0]
