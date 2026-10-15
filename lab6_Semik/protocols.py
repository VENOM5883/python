"""Протоколы (интерфейсы) приложения."""
from typing import Protocol


class Reportable(Protocol):
    def get_report_data(self) -> str:
        ...


def print_report(item: Reportable) -> None:
    """Принимает любой объект, соответствующий протоколу Reportable."""
    print("[REPORT]", item.get_report_data())
