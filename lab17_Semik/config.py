"""Конфигурация из переменных окружения (токен не хранится в коде)."""
import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    database_path: str = os.getenv("DATABASE_PATH", "clinic_bot.db")
    admin_ids: frozenset[int] = field(default_factory=lambda: frozenset(
        int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()))


config = Config()
