"""Пользовательские исключения."""


class ClinicError(Exception):
    pass


class EntityNotFoundError(ClinicError):
    def __init__(self, entity: str, entity_id: int) -> None:
        super().__init__(f"{entity} с id={entity_id} не найден")


class InvalidStatusTransitionError(ClinicError):
    def __init__(self, current, new) -> None:
        super().__init__(f"Нельзя перевести приём из «{current.value}» в «{new.value}»")


class ValidationError(ClinicError):
    pass
