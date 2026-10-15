"""Валидация входных данных API."""
from datetime import datetime

from exceptions import ValidationError
from models import STATUSES

REQUIRED = ("doctor", "specialty", "date", "time", "cabinet")
ALLOWED = set(REQUIRED) | {"patient", "status"}


def validate(data, partial: bool = False) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Тело запроса должно быть JSON-объектом")
    unknown = set(data) - ALLOWED
    if unknown:
        raise ValidationError(f"Неизвестные поля: {', '.join(sorted(unknown))}")
    if not partial:
        missing = [f for f in REQUIRED if f not in data]
        if missing:
            raise ValidationError(f"Отсутствуют обязательные поля: {', '.join(missing)}")
    if partial and not data:
        raise ValidationError("Нет полей для изменения")
    result = {}
    for key, value in data.items():
        if key in ("doctor", "specialty"):
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"Поле {key} не может быть пустым")
            result[key] = value.strip()
        elif key == "patient":
            result[key] = str(value).strip()
        elif key == "date":
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except (TypeError, ValueError):
                raise ValidationError("date должна быть в формате ГГГГ-ММ-ДД") from None
            result[key] = value
        elif key == "time":
            try:
                datetime.strptime(value, "%H:%M")
            except (TypeError, ValueError):
                raise ValidationError("time должно быть в формате ЧЧ:ММ") from None
            result[key] = value
        elif key == "cabinet":
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValidationError("cabinet должен быть положительным целым числом")
            result[key] = value
        elif key == "status":
            if value not in STATUSES:
                raise ValidationError(f"status должен быть одним из: {', '.join(STATUSES)}")
            result[key] = value
    return result
