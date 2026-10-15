"""Реализации уведомлений (имитация отправки)."""


class ConsoleNotifier:
    def send(self, recipient: str, message: str) -> None:
        print(f"[CONSOLE -> {recipient}] {message}")


class EmailNotifier:
    def __init__(self) -> None:
        self.outbox: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.outbox.append((recipient, message))
        print(f"[EMAIL -> {recipient}] {message}")


class SmsNotifier:
    def send(self, recipient: str, message: str) -> None:
        print(f"[SMS -> {recipient}] {message[:70]}")
