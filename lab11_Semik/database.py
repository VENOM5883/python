"""Подключение к SQLite и инициализация схемы."""
import os
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = os.getenv("DATABASE_PATH", str(BASE / "clinic.db"))


def connect(path: str = DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(connection: sqlite3.Connection, seed: bool = True) -> None:
    connection.executescript((BASE / "sql" / "schema.sql").read_text(encoding="utf-8"))
    empty = connection.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 0
    if seed and empty:
        connection.executescript((BASE / "sql" / "seed.sql").read_text(encoding="utf-8"))
    connection.commit()
