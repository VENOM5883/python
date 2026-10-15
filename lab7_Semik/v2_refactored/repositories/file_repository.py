"""Хранилище в JSON-файле: подменяет InMemoryRepository без изменения сервисов (LSP)."""
import json
from dataclasses import asdict, fields
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


def _encode(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


class FileRepository(Generic[T]):
    def __init__(self, path: Path, entity_type: type[T]) -> None:
        self._path = Path(path)
        self._type = entity_type

    def _load(self) -> dict[int, T]:
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        items = {}
        for data in raw:
            for f in fields(self._type):
                if f.name == "start":
                    data[f.name] = datetime.fromisoformat(data[f.name])
                elif f.name == "status":
                    from models.enums import AppointmentStatus
                    data[f.name] = AppointmentStatus(data[f.name])
            items[data["id"]] = self._type(**data)
        return items

    def _save(self, items: dict[int, T]) -> None:
        data = [{k: _encode(v) for k, v in asdict(item).items()} for item in items.values()]
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def next_id(self) -> int:
        return max(self._load(), default=0) + 1

    def add(self, entity: T) -> T:
        items = self._load()
        items[entity.id] = entity
        self._save(items)
        return entity

    def get(self, entity_id: int) -> T | None:
        return self._load().get(entity_id)

    def get_all(self) -> list[T]:
        return list(self._load().values())

    def remove(self, entity_id: int) -> None:
        items = self._load()
        items.pop(entity_id, None)
        self._save(items)
