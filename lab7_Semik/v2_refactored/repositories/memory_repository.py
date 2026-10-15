from typing import Generic, TypeVar

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[int, T] = {}
        self._last_id = 0

    def next_id(self) -> int:
        self._last_id += 1
        return self._last_id

    def add(self, entity: T) -> T:
        self._items[entity.id] = entity
        self._last_id = max(self._last_id, entity.id)
        return entity

    def get(self, entity_id: int) -> T | None:
        return self._items.get(entity_id)

    def get_all(self) -> list[T]:
        return list(self._items.values())

    def remove(self, entity_id: int) -> None:
        self._items.pop(entity_id, None)
