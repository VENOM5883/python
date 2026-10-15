"""Бизнес-логика каталога компьютерных конфигураций."""
from exceptions import ComputerNotFoundError, DuplicateComputerError
from models import Computer

SORT_KEYS = {
    "price": lambda c: c.price,
    "ram": lambda c: c.ram,
    "storage": lambda c: c.storage,
    "name": lambda c: c.name.lower(),
}


class ComputerCatalog:
    def __init__(self, computers=None):
        self._computers = list(computers or [])

    @property
    def computers(self):
        return list(self._computers)

    def add(self, name, cpu, ram, storage, price):
        if self._find_or_none(name):
            raise DuplicateComputerError(name)
        computer = Computer(name, cpu, ram, storage, price)
        self._computers.append(computer)
        return computer

    def _find_or_none(self, name):
        for computer in self._computers:
            if computer.name.lower() == name.strip().lower():
                return computer
        return None

    def get(self, name):
        computer = self._find_or_none(name)
        if computer is None:
            raise ComputerNotFoundError(name)
        return computer

    def update(self, name, **fields):
        computer = self.get(name)
        for field, value in fields.items():
            if value not in (None, ""):
                setattr(computer, field, value)
        return computer

    def delete(self, name):
        self._computers.remove(self.get(name))

    def search(self, text):
        text = text.lower()
        return [c for c in self._computers if text in c.name.lower() or text in c.cpu.lower()]

    def filter(self, min_ram=0, max_price=None):
        return [c for c in self._computers
                if c.ram >= min_ram and (max_price is None or c.price <= max_price)]

    def sort(self, key="price", descending=False):
        return sorted(self._computers, key=SORT_KEYS[key], reverse=descending)

    def average_price(self):
        if not self._computers:
            return 0.0
        return sum(c.price for c in self._computers) / len(self._computers)
