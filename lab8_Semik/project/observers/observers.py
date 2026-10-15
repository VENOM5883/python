"""Observer: независимые наблюдатели за событиями записи."""
from collections import Counter

from models.entities import Appointment


class LoggerObserver:
    def __init__(self) -> None:
        self.records: list[str] = []

    def update(self, event: str, appointment: Appointment) -> None:
        line = f"[LOG] {event}: запись #{appointment.id} ({appointment.status.value})"
        self.records.append(line)
        print(line)


class NotificationObserver:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def update(self, event: str, appointment: Appointment) -> None:
        text = f"[УВЕДОМЛЕНИЕ -> {appointment.patient}] {event}: {appointment.title}, " \
               f"{appointment.start:%d.%m %H:%M}"
        self.sent.append(text)
        print(text)


class StatisticsObserver:
    def __init__(self) -> None:
        self.events: Counter = Counter()
        self.revenue = 0.0

    def update(self, event: str, appointment: Appointment) -> None:
        self.events[event] += 1
        if event == "приём завершён":
            self.revenue += appointment.price
