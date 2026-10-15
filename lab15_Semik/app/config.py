import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///pharmacy_web.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
