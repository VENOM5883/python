"""Иерархия ошибок приложения и централизованная обработка."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class EntityNotFoundError(AppError):
    status_code, code = 404, "NOT_FOUND"


class ValidationAppError(AppError):
    status_code, code = 400, "VALIDATION_ERROR"


class BusinessRuleError(AppError):
    status_code, code = 409, "BUSINESS_RULE_VIOLATION"


class AuthError(AppError):
    status_code, code = 401, "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code, code = 403, "FORBIDDEN"


def register_handlers(app: FastAPI, log) -> None:
    @app.exception_handler(AppError)
    async def app_error(_: Request, error: AppError):
        return JSONResponse(status_code=error.status_code, content={"error": error.code, "message": error.message},
                            headers={"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, error: Exception):
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR", "message": "Internal server error"})
