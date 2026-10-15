"""Лабораторная работа №18. Вариант 15 — Медицинский центр, система записи на приём.
Консольный интерфейс.  Запуск из папки lab18_Semik:  python -m src.main
"""
from datetime import datetime, timedelta

from src.exceptions import ClinicError
from src.repositories.sqlite_repository import ClinicRepository
from src.services.clinic_service import ClinicService
from src.services.notifier import SmsNotifier


def main() -> None:
    service = ClinicService(ClinicRepository("clinic18.db"), SmsNotifier())
    menu = ("\n1. Регистрация пациента\n2. Добавить врача\n3. Свободное время врача\n4. Создать запись\n"
            "5. Отменить запись\n6. История пациента\n0. Выход")
    while True:
        print(menu)
        choice = input("Выбор: ").strip()
        try:
            if choice == "1":
                print(service.register_patient(input("ФИО: "), input("Телефон (+7...): ")))
            elif choice == "2":
                print(service.add_doctor(input("ФИО: "), input("Специальность: "), int(input("Длительность приёма, мин: "))))
            elif choice == "3":
                day = input("Дата (ГГГГ-ММ-ДД, Enter — завтра): ").strip() or (datetime.now() + timedelta(days=1)).date().isoformat()
                print(", ".join(service.free_slots(int(input("ID врача: ")), day)))
            elif choice == "4":
                start = datetime.strptime(input("Дата и время (ГГГГ-ММ-ДД ЧЧ:ММ): "), "%Y-%m-%d %H:%M")
                print(service.create_appointment(int(input("ID пациента: ")), int(input("ID врача: ")), start))
            elif choice == "5":
                print(service.cancel_appointment(int(input("ID записи: "))))
            elif choice == "6":
                for appointment in service.patient_history(int(input("ID пациента: "))):
                    print(" ", appointment)
            elif choice == "0":
                break
        except (ClinicError, ValueError) as error:
            print("Ошибка:", error)


if __name__ == "__main__":
    main()
