"""Генераторы и собственный итератор."""


def computers_of_type(computers, computer_type):
    """Генератор компьютеров определённого типа."""
    for computer in computers:
        if isinstance(computer, computer_type):
            yield computer


def price_range(computers, low, high):
    for computer in computers:
        if low <= computer.price <= high:
            yield computer


class ComputerIterator:
    """Итератор, выдающий компьютеры по возрастанию цены."""

    def __init__(self, computers):
        self._computers = sorted(computers, key=lambda c: c.price)
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._computers):
            raise StopIteration
        computer = self._computers[self._index]
        self._index += 1
        return computer
