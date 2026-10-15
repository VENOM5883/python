import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./pharmacy.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-only-secret-change-me-in-production-0123456789")
    jwt_ttl_minutes: int = int(os.getenv("JWT_TTL_MINUTES", "60"))
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@pharmacy.local")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin12345")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
