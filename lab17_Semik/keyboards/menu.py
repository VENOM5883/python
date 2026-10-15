from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

DOCTORS_BTN = "👨‍⚕️ Врачи"
BOOK_BTN = "📝 Записаться"
MY_BTN = "📋 Мои записи"
HISTORY_BTN = "🗂 История посещений"
SEARCH_BTN = "🔎 Поиск врача"
HELP_BTN = "ℹ️ Помощь"

main_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=DOCTORS_BTN), KeyboardButton(text=BOOK_BTN)],
              [KeyboardButton(text=MY_BTN), KeyboardButton(text=HISTORY_BTN)],
              [KeyboardButton(text=SEARCH_BTN), KeyboardButton(text=HELP_BTN)]],
    resize_keyboard=True, input_field_placeholder="Выберите действие")

cancel_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True)
