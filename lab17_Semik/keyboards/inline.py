from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SpecialtyCb(CallbackData, prefix="spec"):
    name: str


class DoctorCb(CallbackData, prefix="doc"):
    id: int


class TimeCb(CallbackData, prefix="time"):
    value: str


class AppointmentCb(CallbackData, prefix="app"):
    action: str   # show / edit / cancel / delete
    id: int


def specialties_kb(specialties: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name in specialties:
        builder.button(text=name.capitalize(), callback_data=SpecialtyCb(name=name))
    return builder.adjust(2).as_markup()


def doctors_kb(doctors: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for doctor in doctors:
        builder.button(text=f"{doctor['full_name']} (каб. {doctor['cabinet']})", callback_data=DoctorCb(id=doctor["id"]))
    return builder.adjust(1).as_markup()


def times_kb(times: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in times:
        builder.button(text=value, callback_data=TimeCb(value=value.replace(":", "-")))
    return builder.adjust(4).as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="booking:confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="booking:cancel")]])


def appointments_kb(appointments: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for a in appointments:
        builder.button(text=f"{a['date']} {a['time']} — {a['specialty']}",
                       callback_data=AppointmentCb(action="show", id=a["id"]))
    return builder.adjust(1).as_markup()


def appointment_actions_kb(appointment: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if appointment["status"] == "planned":
        builder.button(text="✏️ Изменить жалобу", callback_data=AppointmentCb(action="edit", id=appointment["id"]))
        builder.button(text="🚫 Отменить запись", callback_data=AppointmentCb(action="cancel", id=appointment["id"]))
    else:
        builder.button(text="🗑 Удалить из истории", callback_data=AppointmentCb(action="delete", id=appointment["id"]))
    return builder.adjust(1).as_markup()
