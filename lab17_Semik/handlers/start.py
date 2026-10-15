"""/start, /help, /cancel, регистрация пациента (FSM из 2 шагов)."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.menu import HELP_BTN, cancel_menu, main_menu
from services.clinic_service import ClinicError, ClinicService
from states.booking import Registration

router = Router(name="start")

HELP_TEXT = ("Я бот медицинской клиники (учебный проект, данные вымышленные).\n\n"
             "/start — начало работы и регистрация\n/help — помощь\n/cancel — отменить текущее действие\n"
             "/doctors — список врачей\n/book — записаться на приём\n/my — мои записи\n"
             "/history — история посещений\n/find — поиск врача")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, service: ClinicService) -> None:
    await state.clear()
    patient = await service.get_patient(message.from_user.id)
    if patient:
        await message.answer(f"Здравствуйте, {patient['full_name']}! Выберите действие.", reply_markup=main_menu)
        return
    await state.set_state(Registration.full_name)
    await message.answer("Добро пожаловать в клинику! Для записи на приём зарегистрируйтесь.\n"
                         "Введите фамилию и имя:", reply_markup=cancel_menu)


@router.message(Command("help"))
@router.message(F.text == HELP_BTN)
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu)


@router.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    text = "Действие отменено." if current else "Нечего отменять."
    await message.answer(text, reply_markup=main_menu)


@router.message(Registration.full_name, F.text)
async def reg_name(message: Message, state: FSMContext) -> None:
    from services.clinic_service import validate_name
    try:
        await state.update_data(full_name=validate_name(message.text))
    except ClinicError as error:
        await message.answer(str(error))
        return
    await state.set_state(Registration.phone)
    await message.answer("Введите номер телефона в формате +7XXXXXXXXXX:")


@router.message(Registration.phone, F.text)
async def reg_phone(message: Message, state: FSMContext, service: ClinicService) -> None:
    data = await state.get_data()
    try:
        patient = await service.register(message.from_user.id, data["full_name"], message.text)
    except ClinicError as error:
        await message.answer(str(error))
        return
    await state.clear()
    await message.answer(f"Регистрация завершена, {patient['full_name']}!", reply_markup=main_menu)


@router.message(StateFilter(Registration), ~F.text)
async def reg_wrong_type(message: Message) -> None:
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")
