"""Лабораторная работа №1. Основы программирования на Python.
Вариант 15. Интернет-магазин: анализ заказов.
"""
import random


def read_int(prompt, minimum=None):
    """Читает целое число с проверкой минимального значения."""
    while True:
        text = input(prompt).strip()
        if not text.lstrip("-").isdigit():
            print("Ошибка: необходимо ввести целое число")
            continue
        value = int(text)
        if minimum is not None and value < minimum:
            print(f"Ошибка: значение не может быть меньше {minimum}")
            continue
        return value


def read_float(prompt, minimum=0.0):
    """Читает вещественное число, не меньшее minimum."""
    while True:
        text = input(prompt).strip().replace(",", ".")
        try:
            value = float(text)
        except ValueError:
            print("Ошибка: необходимо ввести число")
            continue
        if value < minimum:
            print("Ошибка: значение не может быть отрицательным")
            continue
        return value


def input_orders():
    """Ввод стоимости заказов вручную или случайным образом."""
    count = read_int("Введите количество заказов: ", 1)
    mode = input("Сгенерировать стоимости случайно? (д/н): ").strip().lower()
    orders = []
    for i in range(count):
        if mode == "д":
            orders.append(round(random.uniform(300, 15000), 2))
        else:
            orders.append(read_float(f"Стоимость заказа {i + 1}: "))
    return orders


def calculate_total(orders):
    total = 0
    for price in orders:
        total += price
    return total


def calculate_average(orders):
    return calculate_total(orders) / len(orders)


def find_maximum(orders):
    maximum = orders[0]
    number = 1
    for i in range(1, len(orders)):
        if orders[i] > maximum:
            maximum = orders[i]
            number = i + 1
    return number, maximum


def count_above_average(orders):
    average = calculate_average(orders)
    count = 0
    for price in orders:
        if price > average:
            count += 1
    return count


def calculate_discounts(orders, threshold, percent):
    """Возвращает список (номер, стоимость, скидка, итог) для заказов дороже порога."""
    result = []
    for i, price in enumerate(orders, start=1):
        if price > threshold:
            discount = round(price * percent / 100, 2)
            result.append((i, price, discount, round(price - discount, 2)))
    return result


def print_statistics(orders):
    number, maximum = find_maximum(orders)
    print("\n===== Результаты анализа =====")
    for i, price in enumerate(orders, start=1):
        print(f"Заказ {i}: {price:.2f} руб.")
    print(f"Общая сумма заказов: {calculate_total(orders):.2f} руб.")
    print(f"Средняя стоимость заказа: {calculate_average(orders):.2f} руб.")
    print(f"Максимальный заказ: №{number} — {maximum:.2f} руб.")
    print(f"Заказов дороже среднего: {count_above_average(orders)}")


def print_discounts(orders):
    threshold = read_float("Сумма, после которой предоставляется скидка: ")
    while True:
        percent = read_float("Размер скидки, %: ")
        if percent <= 100:
            break
        print("Ошибка: процент должен быть в диапазоне от 0 до 100")
    discounts = calculate_discounts(orders, threshold, percent)
    if not discounts:
        print("Нет заказов, превышающих заданную сумму.")
        return
    total_discount = 0
    for number, price, discount, final in discounts:
        total_discount += discount
        print(f"Заказ {number}: {price:.2f} − {discount:.2f} = {final:.2f} руб.")
    print(f"Скидка предоставлена по {len(discounts)} заказам, "
          f"общая сумма скидок: {total_discount:.2f} руб.")


def main():
    print("Анализ заказов интернет-магазина")
    orders = input_orders()
    print_statistics(orders)
    print_discounts(orders)


if __name__ == "__main__":
    main()
