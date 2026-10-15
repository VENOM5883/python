"""Хранилище полисов в памяти процесса (потокобезопасное)."""
import threading

from exceptions import PolicyNotFoundError
from models import Policy


class PolicyRepository:
    def __init__(self) -> None:
        self._items: dict[int, Policy] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def add(self, data: dict) -> Policy:
        with self._lock:
            policy = Policy(id=self._next_id, **data)
            self._items[policy.id] = policy
            self._next_id += 1
            return policy

    def get(self, policy_id: int) -> Policy:
        with self._lock:
            if policy_id not in self._items:
                raise PolicyNotFoundError(policy_id)
            return self._items[policy_id]

    def get_all(self) -> list[Policy]:
        with self._lock:
            return list(self._items.values())

    def update(self, policy_id: int, fields: dict) -> Policy:
        with self._lock:
            if policy_id not in self._items:
                raise PolicyNotFoundError(policy_id)
            policy = self._items[policy_id]
            for key, value in fields.items():
                setattr(policy, key, value)
            return policy

    def delete(self, policy_id: int) -> None:
        with self._lock:
            if self._items.pop(policy_id, None) is None:
                raise PolicyNotFoundError(policy_id)
