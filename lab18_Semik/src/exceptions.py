class ClinicError(Exception):
    """Базовое исключение."""


class NotFoundError(ClinicError):
    pass


class ValidationError(ClinicError):
    pass


class SlotUnavailableError(ClinicError):
    """Врач уже занят в это время."""
