"""Контекстные менеджеры."""
import copy
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

LOG_PATH = Path(__file__).with_name("operations.log")


class OperationLogger:
    """Записывает в файл дату, операцию, параметры, длительность и результат."""

    def __init__(self, operation: str, path: Path = LOG_PATH, **params) -> None:
        self.operation = operation
        self.path = path
        self.params = params

    def __enter__(self) -> "OperationLogger":
        self._start = time.perf_counter()
        print(f"[CONTEXT] начало операции {self.operation}")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        duration = time.perf_counter() - self._start
        lines = [f"[{datetime.now():%Y-%m-%d %H:%M:%S}]", f"Operation: {self.operation}",
                 f"Params: {self.params}", f"Duration: {duration:.4f} sec",
                 f"Result: {'ERROR' if exc_type else 'SUCCESS'}"]
        if exc_type:
            lines.append(f"Exception: {exc_type.__name__}: {exc_value}")
        with open(self.path, "a", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n\n")
        print(f"[CONTEXT] завершение операции {self.operation}: "
              f"{'ERROR' if exc_type else 'SUCCESS'} за {duration:.4f} сек")
        return False  # исключение не подавляется


@contextmanager
def transaction(clinic) -> Iterator[None]:
    """Транзакционный режим: при ошибке состояние клиники откатывается."""
    snapshot = copy.deepcopy(clinic.__dict__)
    try:
        yield
        print("[TRANSACTION] COMMIT")
    except Exception:
        clinic.__dict__.clear()
        clinic.__dict__.update(snapshot)
        print("[TRANSACTION] ROLLBACK")
        raise
