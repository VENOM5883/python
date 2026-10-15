class ApiError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ApiError):
    status_code = 404
    code = "APPOINTMENT_NOT_FOUND"


class ValidationError(ApiError):
    status_code = 400
    code = "VALIDATION_ERROR"


class ConflictError(ApiError):
    status_code = 409
    code = "CONFLICT"
