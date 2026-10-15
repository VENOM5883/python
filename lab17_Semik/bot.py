"""Лабораторная работа №17. Telegram-бот на aiogram 3.
Вариант 15. Медицинская клиника: пациенты, врачи, приёмы, диагнозы (учебные данные).
Запуск: заполнить .env (BOT_TOKEN) и выполнить  python bot.py
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.db import connect, init_db
from database.repository import ClinicRepository
from handlers import admin, appointments, booking, doctors, fallback, start
from middlewares.logging import LoggingMiddleware
from services.clinic_service import ClinicService


def build_dispatcher(service: ClinicService, admin_ids: frozenset[int] = frozenset()) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp["service"] = service          # зависимости, доступные в обработчиках
    dp["admin_ids"] = admin_ids
    middleware = LoggingMiddleware()
    dp.message.outer_middleware(middleware)
    dp.callback_query.outer_middleware(middleware)
    dp.include_routers(start.router, booking.router, appointments.router, doctors.router, admin.router,
                       fallback.router)
    return dp


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not config.bot_token:
        raise SystemExit("Не задан BOT_TOKEN (см. .env.example)")
    connection = connect(config.database_path)
    init_db(connection)
    dp = build_dispatcher(ClinicService(ClinicRepository(connection)), config.admin_ids)
    bot = Bot(config.bot_token)
    logging.info("Бот запущен (polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
