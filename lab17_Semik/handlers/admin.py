"""Команды администратора."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.clinic_service import ClinicService

router = Router(name="admin")


@router.message(Command("stats"))
async def stats(message: Message, service: ClinicService, admin_ids: frozenset[int]) -> None:
    if message.from_user.id not in admin_ids:
        await message.answer("Команда доступна только администратору.")
        return
    counts = await service.statistics()
    await message.answer("Статистика БД:\n" + "\n".join(f"{k}: {v}" for k, v in counts.items()))
