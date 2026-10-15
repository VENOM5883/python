"""Интроспекция объектов."""
import inspect
from dataclasses import fields, is_dataclass

from models import Entity, Person


def inspect_object(obj: object) -> str:
    lines = ["=== ИНФОРМАЦИЯ ОБ ОБЪЕКТЕ ===",
             f"Тип: {type(obj).__name__}",
             f"Сущность (isinstance Entity): {isinstance(obj, Entity)}",
             f"Класс — потомок Person (issubclass): {issubclass(type(obj), Person)}"]
    if hasattr(obj, "id"):
        lines.append(f"ID: {getattr(obj, 'id')}")
    if is_dataclass(obj):
        lines.append("Атрибуты:")
        lines += [f"  {f.name}: {f.type} = {getattr(obj, f.name)!s:.60}" for f in fields(obj)]
    lines.append("Методы:")
    for name, member in inspect.getmembers(obj, predicate=inspect.ismethod):
        if not name.startswith("_"):
            lines.append(f"  {name}{inspect.signature(member)}")
    public = [name for name in dir(obj) if not name.startswith("_")]
    lines.append(f"Всего публичных имён (dir): {len(public)}")
    return "\n".join(lines)
