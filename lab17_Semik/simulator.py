"""Имитация Telegram без сети: события подаются в Dispatcher, а ответы бота
перехватываются подменённой HTTP-сессией aiogram и печатаются в консоль.
Используется для проверки работоспособности и для тестов.  Запуск: python simulator.py
"""
import asyncio
import itertools
from datetime import datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendMessage
from aiogram.types import CallbackQuery, Chat, InlineKeyboardMarkup, Message, Update, User

FAKE_TOKEN = "123456:SIMULATED-TOKEN-NOT-REAL"


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.sent: list = []
        self._ids = itertools.count(1000)

    async def make_request(self, bot, method, timeout=None):
        self.sent.append(method)
        if isinstance(method, (SendMessage, EditMessageText)):
            return Message(message_id=next(self._ids), date=datetime.now(),
                           chat=Chat(id=method.chat_id or 1, type="private"), text=method.text,
                           reply_markup=method.reply_markup if isinstance(method.reply_markup, InlineKeyboardMarkup) else None)
        if isinstance(method, AnswerCallbackQuery):
            return True
        return True

    async def stream_content(self, *args, **kwargs):  # pragma: no cover
        yield b""

    async def close(self) -> None:
        pass


class TelegramSimulator:
    def __init__(self, dispatcher, user_id: int = 777, name: str = "Тест") -> None:
        self.dp = dispatcher
        self.session = FakeSession()
        self.bot = Bot(FAKE_TOKEN, session=self.session)
        self.user = User(id=user_id, is_bot=False, first_name=name)
        self.chat = Chat(id=user_id, type="private")
        self._update_ids = itertools.count(1)
        self.last_markup: InlineKeyboardMarkup | None = None

    def _collect(self, start: int) -> list[str]:
        replies = []
        for method in self.session.sent[start:]:
            if isinstance(method, (SendMessage, EditMessageText)):
                replies.append(method.text)
                if isinstance(method.reply_markup, InlineKeyboardMarkup):
                    self.last_markup = method.reply_markup
            elif isinstance(method, AnswerCallbackQuery) and method.text:
                replies.append(f"[alert] {method.text}")
        return replies

    async def send(self, text: str) -> list[str]:
        start = len(self.session.sent)
        message = Message(message_id=next(self._update_ids), date=datetime.now(), chat=self.chat,
                          from_user=self.user, text=text)
        await self.dp.feed_update(self.bot, Update(update_id=next(self._update_ids), message=message))
        return self._collect(start)

    async def press(self, button_text: str) -> list[str]:
        """Нажать inline-кнопку из последней клавиатуры (по началу текста)."""
        button = next(b for row in self.last_markup.inline_keyboard for b in row if b.text.startswith(button_text))
        start = len(self.session.sent)
        message = Message(message_id=1, date=datetime.now(), chat=self.chat, text="...")
        callback = CallbackQuery(id=str(next(self._update_ids)), from_user=self.user, chat_instance="sim",
                                 message=message, data=button.callback_data)
        await self.dp.feed_update(self.bot, Update(update_id=next(self._update_ids), callback_query=callback))
        return self._collect(start)


async def demo() -> None:
    import logging
    from bot import build_dispatcher
    from database.db import connect, init_db
    from database.repository import ClinicRepository
    from services.clinic_service import ClinicService

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    connection = connect(":memory:")
    init_db(connection)
    sim = TelegramSimulator(build_dispatcher(ClinicService(ClinicRepository(connection)), frozenset({777})))

    async def say(text):
        print(f"\n👤 {text}")
        for reply in await sim.send(text):
            print(f"🤖 {reply}")

    async def tap(text):
        print(f"\n👤 [нажата кнопка «{text}»]")
        for reply in await sim.press(text):
            print(f"🤖 {reply}")

    await say("/start")
    await say("123")
    await say("Семик Алексей")
    await say("89001234567")
    await say("👨‍⚕️ Врачи")
    await say("/book")
    await tap("Кардиолог")
    await tap("Кузнецов")
    await say("32.13.2026")
    await say("26.10.2026")
    await tap("10:30")
    await say("Боли в сердце при нагрузке")
    await tap("✅")
    await say("📋 Мои записи")
    await tap("2026-10-26")
    await tap("✏️")
    await say("Боли в сердце, одышка")
    await say("/find")
    await say("невр")
    await say("/stats")
    await say("привет")


if __name__ == "__main__":
    asyncio.run(demo())
