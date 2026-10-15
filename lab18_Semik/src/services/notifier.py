class SmsNotifier:
    """Внешний сервис SMS (в учебном проекте только печатает сообщение)."""

    def send(self, phone: str, text: str) -> bool:
        print(f"[SMS {phone}] {text}")
        return True
