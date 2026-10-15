"""Многошаговая запись на приём (FSM): специальность → врач → дата → время → жалобы → подтверждение."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.inline import DoctorCb, SpecialtyCb, TimeCb, confirm_kb, doctors_kb, specialties_kb, times_kb
from keyboards.menu import BOOK_BTN, cancel_menu, main_menu
from services.clinic_service import ClinicError, ClinicService, validate_date
from states.booking import Booking

router = Router(name="booking")


@router.message(Command("book"))
@router.message(F.text == BOOK_BTN)
async def booking_start(message: Message, state: FSMContext, service: ClinicService) -> None:
    if await service.get_patient(message.from_user.id) is None:
        await message.answer("Сначала зарегистрируйтесь: отправьте /start")
        return
    await state.set_state(Booking.specialty)
    await message.answer("Запись на приём. Для отмены — /cancel", reply_markup=cancel_menu)
    await message.answer("Выберите специальность:", reply_markup=specialties_kb(await service.specialties()))


@router.callback_query(Booking.specialty, SpecialtyCb.filter())
async def choose_specialty(callback: CallbackQuery, callback_data: SpecialtyCb, state: FSMContext,
                           service: ClinicService) -> None:
    await state.update_data(specialty=callback_data.name)
    await state.set_state(Booking.doctor)
    await callback.message.edit_text(f"Специальность: {callback_data.name}. Выберите врача:",
                                     reply_markup=doctors_kb(await service.doctors(callback_data.name)))
    await callback.answer()


@router.callback_query(Booking.doctor, DoctorCb.filter())
async def choose_doctor(callback: CallbackQuery, callback_data: DoctorCb, state: FSMContext,
                        service: ClinicService) -> None:
    doctor = await service.doctor(callback_data.id)
    await state.update_data(doctor_id=doctor["id"], doctor_name=doctor["full_name"])
    await state.set_state(Booking.date)
    await callback.message.edit_text(f"Врач: {doctor['full_name']}.\nВведите дату приёма (ДД.ММ.ГГГГ):")
    await callback.answer()


@router.message(Booking.date, F.text)
async def enter_date(message: Message, state: FSMContext, service: ClinicService) -> None:
    try:
        date_iso = validate_date(message.text)
    except ClinicError as error:
        await message.answer(str(error))
        return
    data = await state.get_data()
    times = await service.free_times(data["doctor_id"], date_iso)
    if not times:
        await message.answer("На эту дату свободного времени нет, введите другую дату.")
        return
    await state.update_data(date=date_iso)
    await state.set_state(Booking.time)
    await message.answer("Выберите время:", reply_markup=times_kb(times))


@router.callback_query(Booking.time, TimeCb.filter())
async def choose_time(callback: CallbackQuery, callback_data: TimeCb, state: FSMContext) -> None:
    await state.update_data(time=callback_data.value.replace("-", ":"))
    await state.set_state(Booking.complaint)
    await callback.message.edit_text(f"Время: {callback_data.value.replace('-', ':')}.\nОпишите кратко жалобы:")
    await callback.answer()


@router.message(Booking.complaint, F.text)
async def enter_complaint(message: Message, state: FSMContext) -> None:
    if len(message.text.strip()) < 3:
        await message.answer("Опишите жалобы подробнее (минимум 3 символа).")
        return
    await state.update_data(complaint=message.text.strip())
    data = await state.get_data()
    await state.set_state(Booking.confirm)
    await message.answer(f"Проверьте данные:\nВрач: {data['doctor_name']} ({data['specialty']})\n"
                         f"Дата и время: {data['date']} {data['time']}\nЖалобы: {data['complaint']}",
                         reply_markup=confirm_kb())


@router.callback_query(Booking.confirm, F.data == "booking:confirm")
async def confirm(callback: CallbackQuery, state: FSMContext, service: ClinicService) -> None:
    data = await state.get_data()
    try:
        appointment = await service.book(callback.from_user.id, data["doctor_id"], data["date"], data["time"],
                                         data["complaint"])
    except ClinicError as error:
        await callback.answer(str(error), show_alert=True)
        await state.set_state(Booking.date)
        await callback.message.answer("Введите другую дату (ДД.ММ.ГГГГ):")
        return
    await state.clear()
    await callback.message.edit_text(f"✅ Вы записаны! Запись №{appointment['id']}: {appointment['date']} "
                                     f"{appointment['time']}, {appointment['doctor']}, каб. {appointment['cabinet']}")
    await callback.message.answer("Главное меню", reply_markup=main_menu)
    await callback.answer()


@router.callback_query(Booking.confirm, F.data == "booking:cancel")
async def confirm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Запись отменена.")
    await callback.message.answer("Главное меню", reply_markup=main_menu)
    await callback.answer()


@router.message(Booking.date)
@router.message(Booking.complaint)
async def wrong_content_type(message: Message) -> None:
    await message.answer("Ожидается текстовое сообщение.")


@router.message(Booking.specialty)
@router.message(Booking.doctor)
@router.message(Booking.time)
@router.message(Booking.confirm)
async def use_buttons(message: Message) -> None:
    await message.answer("Пожалуйста, используйте кнопки под сообщением или /cancel.")
