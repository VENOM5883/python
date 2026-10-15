"""Паттерны отказоустойчивости: Retry (с exponential backoff) и Circuit Breaker."""
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import httpx

log = logging.getLogger("resilience")


class ServiceUnavailableError(Exception):
    """Зависимый сервис недоступен (после повторов или при открытом Circuit Breaker)."""


class CircuitOpenError(ServiceUnavailableError):
    pass


RETRY_STATUSES = {502, 504}          # шлюз/прокси не дождался сервиса
IDEMPOTENT = {"GET", "PUT", "DELETE", "HEAD"}


def is_retryable(error: Exception) -> bool:
    if isinstance(error, httpx.TransportError):        # нет соединения, тайм-аут
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in RETRY_STATUSES
    return False


def retry(func: Callable[[], Any], attempts: int = 3, base_delay: float = 0.2, factor: float = 2.0,
          name: str = "call") -> Any:
    """Повтор запроса: ограниченное число попыток, задержка растёт экспоненциально."""
    delay = base_delay
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as error:  # noqa: BLE001
            if not is_retryable(error) or attempt == attempts:
                if is_retryable(error):
                    log.error("%s: все %d попыток неудачны: %s", name, attempts, error)
                    raise ServiceUnavailableError(f"{name}: сервис недоступен") from error
                raise
            log.warning("%s: попытка %d/%d неудачна (%s), повтор через %.1f c", name, attempt, attempts,
                        type(error).__name__, delay)
            time.sleep(delay)
            delay *= factor


class CircuitBreaker:
    CLOSED, OPEN, HALF_OPEN = "CLOSED", "OPEN", "HALF_OPEN"

    def __init__(self, name: str, failure_threshold: int = 3, reset_timeout: float = 10.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.clock = clock
        self.state = self.CLOSED
        self.failures = 0
        self.opened_at = 0.0
        self._lock = threading.Lock()

    def call(self, func: Callable[[], Any]) -> Any:
        with self._lock:
            if self.state == self.OPEN:
                if self.clock() - self.opened_at >= self.reset_timeout:
                    self.state = self.HALF_OPEN
                    log.info("CircuitBreaker[%s]: OPEN -> HALF_OPEN (пробный запрос)", self.name)
                else:
                    raise CircuitOpenError(f"{self.name}: Circuit Breaker открыт, запрос не выполняется")
        try:
            result = func()
        except ServiceUnavailableError:
            self._on_failure()
            raise
        except Exception as error:
            if is_retryable(error):
                self._on_failure()
                raise ServiceUnavailableError(f"{self.name}: сервис недоступен") from error
            raise
        self._on_success()
        return result

    def _on_failure(self) -> None:
        with self._lock:
            self.failures += 1
            if self.state == self.HALF_OPEN or self.failures >= self.failure_threshold:
                if self.state != self.OPEN:
                    log.error("CircuitBreaker[%s]: -> OPEN после %d ошибок", self.name, self.failures)
                self.state = self.OPEN
                self.opened_at = self.clock()

    def _on_success(self) -> None:
        with self._lock:
            if self.state != self.CLOSED:
                log.info("CircuitBreaker[%s]: -> CLOSED (сервис восстановлен)", self.name)
            self.state = self.CLOSED
            self.failures = 0

    def status(self) -> dict:
        return {"name": self.name, "state": self.state, "failures": self.failures}


class ResilientClient:
    """HTTP-клиент к другому сервису: тайм-аут + Retry + Circuit Breaker."""

    def __init__(self, name: str, base_url: str, timeout: float = 2.0, attempts: int = 3,
                 breaker: CircuitBreaker | None = None, transport: httpx.BaseTransport | None = None) -> None:
        self.name = name
        self.client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)
        self.attempts = attempts
        self.breaker = breaker or CircuitBreaker(name)

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        def send() -> httpx.Response:
            response = self.client.request(method, url, **kwargs)
            # 502/504 повторяем только для идемпотентных методов; остальные ответы живого сервиса
            # (в т.ч. 500/503) возвращаются вызывающему как есть
            if response.status_code in RETRY_STATUSES and method.upper() in IDEMPOTENT:
                response.raise_for_status()
            return response
        return self.breaker.call(lambda: retry(send, self.attempts, name=f"{self.name} {method} {url}"))
