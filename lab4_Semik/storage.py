"""Сохранение и загрузка каталога (JSON, CSV)."""
import csv
import json
import os

from exceptions import StorageError
from models import Computer

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
JSON_PATH = os.path.join(DATA_DIR, "computers.json")
CSV_PATH = os.path.join(DATA_DIR, "computers.csv")
CSV_FIELDS = ["name", "cpu", "ram", "storage", "price"]


def load_json(path=JSON_PATH):
    """Загружает компьютеры. Если файла нет — возвращает пустой список."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise StorageError(f"Файл {path} содержит некорректный JSON: {error}") from error
    try:
        return [Computer.from_dict(item) for item in data]
    except (KeyError, TypeError, ValueError) as error:
        raise StorageError(f"Некорректная запись в {path}: {error}") from error


def save_json(computers, path=JSON_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump([c.to_dict() for c in computers], file, ensure_ascii=False, indent=4)


def export_csv(computers, path=CSV_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for computer in computers:
            writer.writerow(computer.to_dict())
