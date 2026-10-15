from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    full_name = State()
    phone = State()


class Booking(StatesGroup):
    specialty = State()   # 1. выбор специальности
    doctor = State()      # 2. выбор врача
    date = State()        # 3. ввод даты
    time = State()        # 4. выбор времени
    complaint = State()   # 5. жалобы
    confirm = State()     # 6. подтверждение


class EditComplaint(StatesGroup):
    text = State()


class SearchDoctor(StatesGroup):
    query = State()
