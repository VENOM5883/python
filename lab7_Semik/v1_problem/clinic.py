"""Версия 1 (до рефакторинга): работающая программа с намеренными нарушениями SOLID.
Вариант 15. Медицинская клиника.

Проблемы отмечены комментариями «НАРУШЕНИЕ».
"""
import json
from datetime import datetime


class Person:
    def __init__(self, name):
        self.name = name

    # НАРУШЕНИЕ LSP: базовый класс обещает поведение, которое есть не у всех наследников
    def prescribe(self, patient, medicine):
        raise NotImplementedError


class Doctor(Person):
    def __init__(self, name, specialty):
        super().__init__(name)
        self.specialty = specialty

    def prescribe(self, patient, medicine):
        return f"{self.name} назначил {medicine} пациенту {patient.name}"


class Patient(Person):
    def prescribe(self, patient, medicine):
        raise NotImplementedError("Пациент не может назначать лечение")


class EmailSender:
    def send(self, to, text):
        print(f"[EMAIL to {to}] {text}")


# НАРУШЕНИЕ ISP: один огромный интерфейс, клиенты зависят от ненужных методов
class ClinicStorageInterface:
    def save_patient(self, patient): ...
    def save_doctor(self, doctor): ...
    def save_appointment(self, appointment): ...
    def load_all(self): ...
    def export_json(self): ...
    def print_report(self): ...
    def send_reminders(self): ...


# НАРУШЕНИЕ SRP: класс одновременно хранит данные, ведёт медицинскую логику,
# рассылает уведомления, формирует отчёт и общается с пользователем.
class ClinicManager(ClinicStorageInterface):
    def __init__(self):
        self.patients = []
        self.doctors = []
        self.appointments = []
        # НАРУШЕНИЕ DIP: жёстко созданная конкретная зависимость
        self.sender = EmailSender()

    def save_patient(self, patient):
        self.patients.append(patient)

    def save_doctor(self, doctor):
        self.doctors.append(doctor)

    def register_patient(self):
        name = input("ФИО пациента: ")  # НАРУШЕНИЕ: бизнес-логика работает с консолью
        patient = Patient(name)
        self.save_patient(patient)
        print("Пациент зарегистрирован")
        return patient

    def book(self, patient, doctor, when):
        for a in self.appointments:
            if a["doctor"] is doctor and a["time"] == when:
                print("Время занято")
                return None
        appointment = {"patient": patient, "doctor": doctor, "time": when, "status": "planned"}
        self.appointments.append(appointment)
        self.sender.send(patient.name, f"Вы записаны к {doctor.name} на {when:%d.%m %H:%M}")
        return appointment

    def conduct(self, appointment, kind):
        # НАРУШЕНИЕ OCP: для нового вида приёма придётся менять этот метод
        if kind == "therapy":
            result = "Осмотр проведён, назначено лечение"
            price = 1500
        elif kind == "diagnostics":
            result = "Проведена диагностика, результаты через 2 дня"
            price = 3000
        elif kind == "consultation":
            result = "Консультация проведена"
            price = 1000
        else:
            raise ValueError("Неизвестный вид приёма")
        appointment["status"] = "completed"
        appointment["result"] = result
        appointment["price"] = price
        self.sender.send(appointment["patient"].name, f"Результат: {result}. К оплате {price} руб.")
        return result

    def export_json(self):
        return json.dumps([{"patient": a["patient"].name, "doctor": a["doctor"].name,
                            "status": a["status"]} for a in self.appointments], ensure_ascii=False)

    def print_report(self):
        for a in self.appointments:
            print(a["patient"].name, "->", a["doctor"].name, a["status"])


def main():
    clinic = ClinicManager()
    doctor = Doctor("Смирнова Е.В.", "терапевт")
    clinic.save_doctor(doctor)
    patient = Patient("Иванов И.И.")
    clinic.save_patient(patient)
    appointment = clinic.book(patient, doctor, datetime(2026, 10, 20, 9, 0))
    clinic.conduct(appointment, "therapy")
    clinic.print_report()
    print(clinic.export_json())
    try:
        people = [doctor, patient]
        for person in people:  # код, ожидающий Person, ломается на Patient
            print(person.prescribe(patient, "витамин D"))
    except NotImplementedError as error:
        print("Нарушение LSP:", error)


if __name__ == "__main__":
    main()
