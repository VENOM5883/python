"""Настройки приложения из переменных окружения."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./clinic.db")
    redis_url: str | None = os.getenv("REDIS_URL")
    app_env: str = os.getenv("APP_ENV", "development")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "120"))


settings = Settings()
