from models.entities import Appointment


class InMemoryRepository:
    def __init__(self) -> None:
        self._items: dict[int, Appointment] = {}

    def add(self, entity: Appointment) -> Appointment:
        self._items[entity.id] = entity
        return entity

    def get(self, entity_id: int) -> Appointment | None:
        return self._items.get(entity_id)

    def get_all(self) -> list[Appointment]:
        return list(self._items.values())

    def delete(self, entity_id: int) -> None:
        if self._items.pop(entity_id, None) is None:
            raise KeyError(f"Запись {entity_id} не найдена")
