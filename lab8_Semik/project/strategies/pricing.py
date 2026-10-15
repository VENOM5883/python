"""Strategy: взаимозаменяемые алгоритмы расчёта стоимости."""
from models.entities import Appointment


class StandardPricing:
    name = "стандартная"

    def calculate(self, appointment: Appointment) -> float:
        return appointment.base_price


class PreferentialPricing:
    """Льготная стоимость (пенсионеры, ветераны): скидка 50 %."""
    name = "льготная"

    def __init__(self, discount: float = 0.5) -> None:
        self.discount = discount

    def calculate(self, appointment: Appointment) -> float:
        return round(appointment.base_price * (1 - self.discount), 2)


class UrgentPricing:
    """Срочный приём: коэффициент 1.8 и фиксированная надбавка."""
    name = "срочная"

    def calculate(self, appointment: Appointment) -> float:
        return round(appointment.base_price * 1.8 + 500, 2)
