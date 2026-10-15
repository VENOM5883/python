"""Небольшие специализированные интерфейсы хранилища (ISP)."""
from typing import Protocol, TypeVar

T = TypeVar("T")


class Readable(Protocol[T]):
    def get(self, entity_id: int) -> T | None: ...
    def get_all(self) -> list[T]: ...


class Writable(Protocol[T]):
    def add(self, entity: T) -> T: ...
    def remove(self, entity_id: int) -> None: ...


class Repository(Readable[T], Writable[T], Protocol[T]):
    def next_id(self) -> int: ...
