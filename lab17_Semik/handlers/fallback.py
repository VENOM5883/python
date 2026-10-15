from aiogram import Router
from aiogram.types import Message

router = Router(name="fallback")


@router.message()
async def unknown(message: Message) -> None:
    await message.answer("Не понимаю сообщение. Воспользуйтесь меню или /help.")
