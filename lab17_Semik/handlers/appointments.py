"""Просмотр, изменение, отмена и удаление записей; история посещений."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards.inline import AppointmentCb, appointment_actions_kb, appointments_kb
from keyboards.menu import HISTORY_BTN, MY_BTN, cancel_menu, main_menu
from services.clinic_service import ClinicError, ClinicService
from states.booking import EditComplaint

router = Router(name="appointments")
STATUS = {"planned": "запланирован", "completed": "завершён", "cancelled": "отменён"}


def describe(a: dict) -> str:
    text = (f"Запись №{a['id']}\n{a['date']} {a['time']}\nВрач: {a['doctor']} ({a['specialty']}), каб. {a['cabinet']}\n"
            f"Жалобы: {a['complaint'] or '—'}\nСтатус: {STATUS[a['status']]}")
    if a.get("diagnosis"):
        text += f"\nДиагноз: {a['diagnosis']}"
    return text


@router.message(Command("my"))
@router.message(F.text == MY_BTN)
async def my_appointments(message: Message, service: ClinicService) -> None:
    appointments = await service.my_appointments(message.from_user.id)
    if not appointments:
        await message.answer("У вас нет запланированных записей. Записаться: /book")
        return
    await message.answer("Ваши записи (нажмите для действий):", reply_markup=appointments_kb(appointments))


@router.message(Command("history"))
@router.message(F.text == HISTORY_BTN)
async def history(message: Message, service: ClinicService) -> None:
    visits = await service.history(message.from_user.id)
    if not visits:
        await message.answer("История посещений пуста.")
        return
    await message.answer("История посещений:\n\n" + "\n\n".join(describe(v) for v in visits),
                         reply_markup=appointments_kb(visits))


@router.callback_query(AppointmentCb.filter(F.action == "show"))
async def show(callback: CallbackQuery, callback_data: AppointmentCb, service: ClinicService) -> None:
    try:
        appointment = await service.appointment(callback.from_user.id, callback_data.id)
    except ClinicError as error:
        await callback.answer(str(error), show_alert=True)  # например, нажата устаревшая кнопка
        return
    await callback.message.answer(describe(appointment), reply_markup=appointment_actions_kb(appointment))
    await callback.answer()


@router.callback_query(AppointmentCb.filter(F.action == "cancel"))
async def cancel(callback: CallbackQuery, callback_data: AppointmentCb, service: ClinicService) -> None:
    try:
        await service.cancel(callback.from_user.id, callback_data.id)
    except ClinicError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.message.edit_text(f"Запись №{callback_data.id} отменена.")
    await callback.answer()


@router.callback_query(AppointmentCb.filter(F.action == "delete"))
async def delete(callback: CallbackQuery, callback_data: AppointmentCb, service: ClinicService) -> None:
    try:
        await service.delete(callback.from_user.id, callback_data.id)
    except ClinicError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await callback.message.edit_text(f"Запись №{callback_data.id} удалена из истории.")
    await callback.answer()


@router.callback_query(AppointmentCb.filter(F.action == "edit"))
async def edit_start(callback: CallbackQuery, callback_data: AppointmentCb, state: FSMContext) -> None:
    await state.set_state(EditComplaint.text)
    await state.update_data(appointment_id=callback_data.id)
    await callback.message.answer("Введите новое описание жалоб:", reply_markup=cancel_menu)
    await callback.answer()


@router.message(EditComplaint.text, F.text)
async def edit_finish(message: Message, state: FSMContext, service: ClinicService) -> None:
    data = await state.get_data()
    try:
        appointment = await service.change_complaint(message.from_user.id, data["appointment_id"], message.text)
    except ClinicError as error:
        await message.answer(str(error))
        return
    await state.clear()
    await message.answer("Изменено:\n" + describe(appointment), reply_markup=main_menu)
