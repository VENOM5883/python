import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.resilience import CircuitBreaker, CircuitOpenError, ServiceUnavailableError, retry  # noqa: E402


def failing(times):
    state = {"calls": 0}

    def func():
        state["calls"] += 1
        if state["calls"] <= times:
            raise httpx.ConnectError("refused")
        return "ok"
    return func, state


def test_retry_succeeds_after_temporary_errors():
    func, state = failing(2)
    assert retry(func, attempts=3, base_delay=0) == "ok" and state["calls"] == 3


def test_retry_gives_up():
    func, state = failing(5)
    with pytest.raises(ServiceUnavailableError):
        retry(func, attempts=3, base_delay=0)
    assert state["calls"] == 3


def test_non_retryable_error_is_not_repeated():
    calls = []

    def func():
        calls.append(1)
        raise ValueError("bad data")
    with pytest.raises(ValueError):
        retry(func, attempts=3, base_delay=0)
    assert len(calls) == 1


def test_circuit_breaker_states():
    now = [0.0]
    breaker = CircuitBreaker("svc", failure_threshold=2, reset_timeout=10, clock=lambda: now[0])
    broken, _ = failing(100)
    for _ in range(2):
        with pytest.raises(ServiceUnavailableError):
            breaker.call(broken)
    assert breaker.state == "OPEN"
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "never called")
    now[0] = 11
    assert breaker.call(lambda: "ok") == "ok"          # HALF_OPEN -> CLOSED
    assert breaker.state == "CLOSED" and breaker.failures == 0


def test_half_open_failure_reopens():
    now = [0.0]
    breaker = CircuitBreaker("svc", failure_threshold=1, reset_timeout=5, clock=lambda: now[0])
    broken, _ = failing(100)
    with pytest.raises(ServiceUnavailableError):
        breaker.call(broken)
    now[0] = 6
    with pytest.raises(ServiceUnavailableError):
        breaker.call(broken)
    assert breaker.state == "OPEN"
