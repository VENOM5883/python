"""Лабораторная работа №5. Функции высшего порядка, итераторы и генераторы.
Вариант 15. Компьютеры.
"""
import sys

from generators import ComputerIterator, computers_of_type, price_range
from models import Desktop, Laptop, Monoblock, create_computers
from operations import (all_cheaper_than, apply_to_computers, cpu_vendors, filter_objects,
                        has_ram, make_ram_filter, most_expensive, price_by_name, process,
                        sort_objects, total_price, transform_objects)

TYPES = {"desktop": Desktop, "laptop": Laptop, "monoblock": Monoblock}


def read_int(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("Ошибка: введите неотрицательное целое число")


def show(computers):
    computers = list(computers)
    for computer in computers:
        print(" ", computer)
    if not computers:
        print("  Нет подходящих компьютеров")


def demo_laziness():
    list_result = [x * x for x in range(1_000_000)]
    generator_result = (x * x for x in range(1_000_000))
    print(f"Список из 1 000 000 квадратов: {sys.getsizeof(list_result):,} байт")
    print(f"Генератор тех же значений:     {sys.getsizeof(generator_result):,} байт")
    print("Генератор вычисляет значения по запросу:", next(generator_result), next(generator_result))


def demo_iterator(computers):
    iterator = ComputerIterator(computers[:3])
    print("next():", next(iterator).name)
    print("next():", next(iterator).name)
    print("next():", next(iterator).name)
    try:
        next(iterator)
    except StopIteration:
        print("Элементы закончились: StopIteration")


def handle(choice, computers):
    if choice == "1":
        show(computers)
    elif choice == "2":
        min_ram = read_int("Минимальный объём RAM, ГБ: ")
        show(filter_objects(computers, make_ram_filter(min_ram)))
    elif choice == "3":
        print("Названия (map):", list(transform_objects(computers, lambda c: c.name)))
        print("Цены (dict comprehension):", price_by_name(computers))
        print("Производители CPU (set comprehension):", cpu_vendors(computers))
    elif choice == "4":
        show(sort_objects(computers, lambda c: c.price))
    elif choice == "5":
        top = most_expensive(computers)
        print(f"Самый дорогой (reduce): {top.name} — {top.price:.2f} руб.")
        print(f"Общая стоимость: {total_price(computers):.2f} руб.")
        print("Цены со скидкой 10%:", apply_to_computers(computers, lambda c: round(c.price * 0.9)))
    elif choice == "6":
        ram = read_int("Объём памяти для проверки, ГБ: ")
        print(f"Есть компьютер с {ram} ГБ RAM (any):", has_ram(computers, ram))
        print("Все дешевле 300 000 руб. (all):", all_cheaper_than(computers, 300_000))
    elif choice == "7":
        kind = input(f"Тип ({', '.join(TYPES)}): ").strip().lower()
        if kind not in TYPES:
            raise KeyError(f"Неизвестный тип «{kind}»")
        show(computers_of_type(computers, TYPES[kind]))
    elif choice == "8":
        low, high = read_int("Цена от: "), read_int("Цена до: ")
        show(price_range(computers, low, high))
    elif choice == "9":
        demo_iterator(computers)
        demo_laziness()
    elif choice == "10":
        pipeline = process(computers, lambda c: c.ram >= 16, lambda c: f"{c.name}: {c.price:.0f}",
                           lambda c: c.price)
        print("Конвейер filter -> sorted -> map:", list(pipeline))
    else:
        print("Неизвестный пункт меню")


def main():
    computers = create_computers()
    menu = ("\n===== МЕНЮ =====\n1. Показать все компьютеры\n2. Фильтр по RAM (filter)\n"
            "3. Преобразовать данные (map, comprehension)\n4. Сортировка по цене\n"
            "5. Самый дорогой и статистика (reduce)\n6. Проверить условие (any/all)\n"
            "7. Генератор компьютеров заданного типа\n8. Генератор по диапазону цены\n"
            "9. Итератор, next() и ленивость\n10. Конвейер обработки\n0. Выход")
    while True:
        print(menu)
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            break
        try:
            handle(choice, computers)
        except (KeyError, ValueError) as error:
            print("Ошибка:", error)


if __name__ == "__main__":
    main()
