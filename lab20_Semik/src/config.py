"""Конфигурация только из переменных окружения."""
import os


def database_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    host = os.getenv("DATABASE_HOST")
    if host:
        return (f"postgresql+psycopg://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}"
                f"@{host}:{os.getenv('DATABASE_PORT', '5432')}/{os.getenv('DATABASE_NAME')}")
    return "sqlite:///./pharmacy.db"


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
