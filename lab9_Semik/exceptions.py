class InsuranceError(Exception):
    """Базовая ошибка предметной области."""


class PolicyNotFoundError(InsuranceError):
    def __init__(self, policy_id: int) -> None:
        super().__init__(f"Policy {policy_id} not found")


class ValidationError(InsuranceError):
    pass


class ProtocolError(Exception):
    """Ошибка формата сообщения прикладного протокола."""
