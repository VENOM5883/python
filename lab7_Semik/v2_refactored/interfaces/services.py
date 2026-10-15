"""Абстракции внешних сервисов и медицинских процедур."""
from abc import ABC, abstractmethod
from typing import Protocol


class Notifier(Protocol):
    def send(self, recipient: str, message: str) -> None: ...


class Procedure(ABC):
    """Вид приёма. Новый вид добавляется новым классом (OCP)."""

    code: str = ""
    title: str = ""

    @abstractmethod
    def perform(self, patient_name: str) -> str: ...

    @abstractmethod
    def price(self) -> float: ...
