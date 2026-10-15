"""Консольный интерфейс — единственное место с input()/print()."""
from datetime import datetime

from procedures.procedures import ALL_PROCEDURES
from services.domain_service import AppointmentService, ClinicError, PatientService, ReportService


class ConsoleUI:
    def __init__(self, patients: PatientService, appointments: AppointmentService,
                 reports: ReportService) -> None:
        self.patients = patients
        self.appointments = appointments
        self.reports = reports

    def run(self) -> None:
        actions = {"1": self.register, "2": self.book, "3": self.assign, "4": self.conduct,
                   "5": self.result, "6": self.summary}
        while True:
            print("\n=== КЛИНИКА ===\n1. Записать пациента (регистрация)\n2. Создать запись на приём\n"
                  "3. Назначить врача\n4. Провести приём\n5. Сформировать результат\n"
                  "6. Сводка\n0. Выход")
            choice = input("Выбор: ").strip()
            if choice == "0":
                return
            try:
                actions.get(choice, lambda: print("Неизвестный пункт"))()
            except (ClinicError, ValueError) as error:
                print("Ошибка:", error)

    def register(self) -> None:
        patient = self.patients.register(input("ФИО: "), input("Телефон: "))
        print(f"Пациент #{patient.id} зарегистрирован")

    def book(self) -> None:
        start = datetime.strptime(input("Дата и время (ДД.ММ.ГГГГ ЧЧ:ММ): "), "%d.%m.%Y %H:%M")
        appointment = self.appointments.book(int(input("ID пациента: ")), start)
        print(f"Создана запись #{appointment.id}")

    def assign(self) -> None:
        self.appointments.assign_doctor(int(input("ID записи: ")), int(input("ID врача: ")))
        print("Врач назначен")

    def conduct(self) -> None:
        code = input(f"Вид приёма ({', '.join(ALL_PROCEDURES)}): ").strip()
        if code not in ALL_PROCEDURES:
            raise ClinicError("Неизвестный вид приёма")
        self.appointments.conduct(int(input("ID записи: ")), ALL_PROCEDURES[code])

    def result(self) -> None:
        print(self.reports.build_result(int(input("ID записи: "))))

    def summary(self) -> None:
        for key, value in self.reports.summary().items():
            print(f"{key}: {value}")
