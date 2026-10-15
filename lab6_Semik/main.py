"""Лабораторная работа №6. Декораторы, контекстные менеджеры и расширенные возможности Python.
Вариант 15. Медицинская клиника: пациенты, врачи, приёмы.
"""
from datetime import datetime

from context import OperationLogger, transaction
from decorators import retry
from exceptions import ClinicError
from introspection import inspect_object
from models import AppointmentStatus
from protocols import Reportable, print_report
from services import ClinicService, create_demo_clinic

MENU = """
===== МЕДИЦИНСКАЯ КЛИНИКА =====
1. Добавить объект (пациент/врач/приём)
2. Удалить объект
3. Найти объект
4. Вывести все объекты
5. Изменить статус приёма
6. Операции варианта (приёмы врача, средняя длительность)
7. Получить статистику
8. Интроспекция объекта
9. Демонстрация декораторов
10. Демонстрация контекстного менеджера
0. Выход"""


def read_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Ошибка: введите целое число")


def show_all(clinic: ClinicService) -> None:
    items: list[Reportable] = [*clinic.patients.values(), *clinic.doctors.values(),
                               *clinic.appointments.values()]
    for item in items:  # объекты разных классов через переменную типа Protocol
        print_report(item)


def add_object(clinic: ClinicService) -> None:
    kind = input("Что добавить (пациент/врач/приём): ").strip().lower()
    if kind == "пациент":
        clinic.add_patient(input("ФИО: "), read_int("Год рождения: "), input("Телефон: "))
    elif kind == "врач":
        clinic.add_doctor(input("ФИО: "), input("Специальность: "), read_int("Кабинет: "),
                          read_int("Стаж, лет: "))
    elif kind == "приём":
        try:
            start = datetime.strptime(input("Дата и время (ДД.ММ.ГГГГ ЧЧ:ММ): "), "%d.%m.%Y %H:%M")
        except ValueError:
            raise ClinicError("Неверный формат даты") from None
        clinic.create_appointment(read_int("ID пациента: "), read_int("ID врача: "), start,
                                  read_int("Длительность, мин: "))
    else:
        print("Неизвестный тип объекта")


def find_object(clinic: ClinicService) -> None:
    text = input("ID или часть ФИО: ").strip()
    if text.isdigit():
        entity_id = int(text)
        for getter in (clinic.get_appointment, clinic.get_patient, clinic.get_doctor):
            try:
                print_report(getter(entity_id))
                return
            except ClinicError:
                continue
        print("Объект не найден")
    else:
        found = clinic.find_by_name(text)
        for person in found:
            print_report(person)
        if not found:
            print("Никого не найдено")


def change_status(clinic: ClinicService) -> None:
    appointment_id = read_int("ID приёма: ")
    statuses = list(AppointmentStatus)
    for i, status in enumerate(statuses, 1):
        print(f"{i}. {status.value}")
    index = read_int("Новый статус: ") - 1
    if not 0 <= index < len(statuses):
        raise ClinicError("Нет такого статуса")
    if statuses[index] is AppointmentStatus.COMPLETED:
        clinic.complete_appointment(appointment_id, input("Заключение врача: "))
    else:
        clinic.change_status(appointment_id, statuses[index])
    print_report(clinic.get_appointment(appointment_id))


def domain_operations(clinic: ClinicService) -> None:
    print("Количество приёмов по врачам:")
    for doctor, count in clinic.count_appointments_by_doctor().items():
        print(f"  {doctor}: {count}")
    print(f"Средняя продолжительность приёма: {clinic.average_duration():.1f} мин")


def demo_decorators(clinic: ClinicService) -> None:
    print("1) @log_call + @wraps:", clinic.add_patient.__name__, "-", clinic.add_patient.__doc__)
    clinic.add_patient("Демонстрационный Пациент", 2000)
    print("2) @timer:")
    clinic.statistics()
    print("3) @require_status(CONFIRMED) для завершения запланированного приёма:")
    planned = next(a for a in clinic.appointments.values()
                   if a.status is AppointmentStatus.PLANNED)
    try:
        clinic.complete_appointment(planned.id, "попытка")
    except ClinicError as error:
        print("  Ошибка:", error)
    print("4) @retry(3) — имитация нестабильного SMS-шлюза:")
    attempts = {"count": 0}

    @retry(3)
    def send_sms(phone: str) -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ConnectionError("шлюз недоступен")
        return f"SMS на {phone} отправлено"

    print(" ", send_sms("+7-900-111-22-33"))


def demo_context(clinic: ClinicService) -> None:
    with OperationLogger("calculate_statistics"):
        clinic.statistics()
    try:
        with OperationLogger("delete_entity", entity_id=999):
            clinic.delete(999)
    except ClinicError as error:
        print("  Ошибка:", error)
    print("Транзакция: создаём пациента и приём с ошибкой — пациент не должен сохраниться")
    before = len(clinic.patients)
    try:
        with transaction(clinic):
            patient = clinic.add_patient("Временный Пациент", 1999)
            clinic.create_appointment(patient.id, 999, datetime.now())
    except ClinicError as error:
        print("  Ошибка:", error)
    print(f"  Пациентов до: {before}, после: {len(clinic.patients)}")


def handle(choice: str, clinic: ClinicService) -> None:
    actions = {
        "1": add_object,
        "2": lambda c: c.delete(read_int("ID объекта: ")),
        "3": find_object,
        "4": show_all,
        "5": change_status,
        "6": domain_operations,
        "7": lambda c: [print(f"  {k}: {v}") for k, v in c.statistics().items()],
        "8": lambda c: print(inspect_object(
            {**c.patients, **c.doctors, **c.appointments}.get(read_int("ID объекта: "), c))),
        "9": demo_decorators,
        "10": demo_context,
    }
    if choice not in actions:
        print("Неизвестный пункт меню")
        return
    actions[choice](clinic)


def main() -> None:
    clinic = create_demo_clinic()
    while True:
        print(MENU)
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            break
        try:
            handle(choice, clinic)
        except (ClinicError, ZeroDivisionError) as error:
            print("Ошибка:", error)


if __name__ == "__main__":
    main()
