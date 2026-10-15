"""Список врачей и поиск."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.menu import DOCTORS_BTN, SEARCH_BTN, cancel_menu, main_menu
from services.clinic_service import ClinicError, ClinicService
from states.booking import SearchDoctor

router = Router(name="doctors")


def format_doctors(doctors: list[dict]) -> str:
    return "\n".join(f"• {d['full_name']} — {d['specialty']}, каб. {d['cabinet']}, стаж {d['experience']} лет"
                     for d in doctors) or "Ничего не найдено."


@router.message(Command("doctors"))
@router.message(F.text == DOCTORS_BTN)
async def list_doctors(message: Message, service: ClinicService) -> None:
    await message.answer("Врачи клиники:\n" + format_doctors(await service.doctors()))


@router.message(Command("find"))
@router.message(F.text == SEARCH_BTN)
async def search_start(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchDoctor.query)
    await message.answer("Введите фамилию врача или специальность:", reply_markup=cancel_menu)


@router.message(SearchDoctor.query, F.text)
async def search_doctor(message: Message, state: FSMContext, service: ClinicService) -> None:
    try:
        found = await service.search_doctors(message.text)
    except ClinicError as error:
        await message.answer(str(error))
        return
    await state.clear()
    await message.answer("Результаты поиска:\n" + format_doctors(found), reply_markup=main_menu)
