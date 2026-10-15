"""Функции обработки коллекций (функции высшего порядка)."""
from functools import reduce


def filter_objects(objects, predicate):
    return filter(predicate, objects)


def transform_objects(objects, operation):
    return map(operation, objects)


def sort_objects(objects, key_function, reverse=False):
    return sorted(objects, key=key_function, reverse=reverse)


def apply_to_computers(computers, operation):
    """Применяет переданную функцию к каждому компьютеру и возвращает список результатов."""
    return [operation(computer) for computer in computers]


def make_ram_filter(min_ram):
    """Возвращает функцию-предикат (функция, возвращающая функцию)."""
    return lambda computer: computer.ram >= min_ram


def most_expensive(computers):
    return reduce(lambda a, b: a if a.price >= b.price else b, computers)


def total_price(computers):
    return reduce(lambda acc, computer: acc + computer.price, computers, 0)


def has_ram(computers, ram):
    return any(computer.ram == ram for computer in computers)


def all_cheaper_than(computers, price):
    return all(computer.price < price for computer in computers)


def price_by_name(computers):
    return {computer.name: computer.price for computer in computers}


def cpu_vendors(computers):
    return {computer.cpu.split()[0] for computer in computers}


def process(objects, predicate, transform, key_function):
    """Конвейер: filter -> sorted -> map, результат выдаётся лениво."""
    for obj in sorted(filter(predicate, objects), key=key_function):
        yield transform(obj)
