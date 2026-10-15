from typing import Protocol

from models.entities import Appointment


class PricingStrategy(Protocol):
    name: str

    def calculate(self, appointment: Appointment) -> float: ...


class Observer(Protocol):
    def update(self, event: str, appointment: Appointment) -> None: ...
