"""Собственные декораторы."""
import time
from functools import wraps
from typing import Any, Callable


def log_call(func: Callable) -> Callable:
    """Журналирование вызова: имя, аргументы, результат."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        shown_args = [repr(a) for a in args[1:]] + [f"{k}={v!r}" for k, v in kwargs.items()]
        print(f"[LOG] вызван {func.__name__}({', '.join(shown_args)})")
        result = func(*args, **kwargs)
        print(f"[LOG] {func.__name__} -> {result!r:.80}")
        return result
    return wrapper


def timer(func: Callable) -> Callable:
    """Измерение времени выполнения."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"[PERFORMANCE] {func.__name__}: {time.perf_counter() - start:.6f} sec")
    return wrapper


def require_status(*statuses) -> Callable:
    """Декоратор с параметрами: операция над приёмом разрешена только в указанных статусах."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, appointment_id: int, *args: Any, **kwargs: Any) -> Any:
            from exceptions import ValidationError
            appointment = self.get_appointment(appointment_id)
            if appointment.status not in statuses:
                allowed = ", ".join(s.value for s in statuses)
                raise ValidationError(
                    f"Операция {func.__name__} доступна только для статусов: {allowed}")
            return func(self, appointment_id, *args, **kwargs)
        return wrapper
    return decorator


def retry(times: int) -> Callable:
    """Декоратор с параметром: повторяет вызов при ошибке."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except ConnectionError as error:
                    print(f"[RETRY] попытка {attempt}/{times} неудачна: {error}")
            raise ConnectionError(f"{func.__name__}: все {times} попытки неудачны")
        return wrapper
    return decorator
