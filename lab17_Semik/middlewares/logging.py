"""Middleware: журнал действий пользователей и время обработки."""
import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

log = logging.getLogger("bot")


class LoggingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        self.counter += 1
        user = getattr(event, "from_user", None)
        if isinstance(event, Message):
            action = event.text or event.content_type
        elif isinstance(event, CallbackQuery):
            action = f"callback {event.data}"
        else:
            action = type(event).__name__
        start = time.perf_counter()
        try:
            return await handler(event, data)
        except Exception:
            log.exception("USER %s %s -> ERROR", user.id if user else "-", action)
            raise
        finally:
            log.info("USER %s %s (%.1f ms, всего событий %d)", user.id if user else "-", action,
                     (time.perf_counter() - start) * 1000, self.counter)
