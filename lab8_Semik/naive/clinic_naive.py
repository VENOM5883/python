"""Этап 1. Наивная реализация без паттернов (вариант 15 — система записи на приём)."""
from datetime import datetime


class ClinicNaive:
    def __init__(self):
        self.appointments = []  # хранение данных прямо внутри сервиса

    def create(self, kind, patient, doctor, start, tariff):
        # создание объектов через if/elif
        if kind == "therapy":
            appointment = {"kind": "Терапевтический приём", "base": 1500, "minutes": 30}
        elif kind == "diagnostics":
            appointment = {"kind": "Диагностическая процедура", "base": 3000, "minutes": 45}
        elif kind == "consultation":
            appointment = {"kind": "Консультация", "base": 1000, "minutes": 20}
        else:
            raise ValueError("Неизвестный тип приёма")
        # выбор алгоритма расчёта через if/elif
        if tariff == "standard":
            price = appointment["base"]
        elif tariff == "preferential":
            price = appointment["base"] * 0.5
        elif tariff == "urgent":
            price = appointment["base"] * 1.8 + 500
        else:
            raise ValueError("Неизвестный тариф")
        appointment.update(patient=patient, doctor=doctor, start=start, price=price, status="создан")
        self.appointments.append(appointment)
        # жёстко зашитые уведомления
        print(f"[EMAIL] {patient}: вы записаны на {start:%d.%m %H:%M}")
        print(f"[LOG] создана запись {appointment['kind']}")
        return appointment


if __name__ == "__main__":
    clinic = ClinicNaive()
    clinic.create("therapy", "Иванов И.И.", "Смирнова Е.В.", datetime(2026, 10, 20, 9), "standard")
    clinic.create("diagnostics", "Петрова А.С.", "Кузнецов О.П.", datetime(2026, 10, 20, 10), "urgent")
    for a in clinic.appointments:
        print(a["kind"], a["patient"], a["price"])
