"""Заполнение БД учебными данными и создание пользователей: python manage.py seed"""
import random
from datetime import date, time, timedelta

from django.contrib.auth.models import Permission, User
from django.core.management.base import BaseCommand

from clinic.models import Appointment, Department, Diagnosis, Doctor, Patient

DEPARTMENTS = [("Терапевтическое", 1), ("Кардиологическое", 2), ("Неврологическое", 3), ("Офтальмологическое", 1)]
DOCTORS = [("Смирнова Елена Викторовна", "терапевт", 101, 12, 0), ("Громов Артём Сергеевич", "терапевт", 102, 5, 0),
           ("Кузнецов Олег Петрович", "кардиолог", 205, 20, 1), ("Орлова Наталья Андреевна", "невролог", 310, 9, 2),
           ("Белова Мария Игоревна", "окулист", 120, 7, 3)]
PATIENTS = ["Иванов Иван Иванович", "Петрова Анна Сергеевна", "Сидоров Павел Олегович", "Новикова Ольга Дмитриевна",
            "Фёдоров Максим Ильич", "Ковалёва Дарья Павловна", "Морозов Кирилл Андреевич", "Волкова Ирина Олеговна"]
DIAGNOSES = [("J06.9", "ОРВИ"), ("I10", "Гипертоническая болезнь"), ("G43.9", "Мигрень"),
             ("H52.1", "Миопия"), ("K29.7", "Гастрит"), ("M54.5", "Боль внизу спины")]
COMPLAINTS = ["Головная боль", "Повышенная температура", "Боль в груди", "Снижение зрения", "Слабость", ""]


class Command(BaseCommand):
    help = "Создаёт отделения, врачей, пациентов, диагнозы, 30 приёмов и пользователей admin/user"

    def handle(self, *args, **options):
        if Appointment.objects.exists():
            self.stdout.write("Данные уже существуют")
            return
        rng = random.Random(15)
        departments = [Department.objects.create(name=n, floor=f) for n, f in DEPARTMENTS]
        doctors = [Doctor.objects.create(full_name=n, specialty=s, cabinet=c, experience=e, department=departments[d])
                   for n, s, c, e, d in DOCTORS]
        patients = [Patient.objects.create(full_name=n, birth_date=date(1960 + i * 5, 1 + i, 10 + i),
                                           phone=f"+7900{1000000 + i:07d}") for i, n in enumerate(PATIENTS)]
        diagnoses = [Diagnosis.objects.create(code=c, title=t) for c, t in DIAGNOSES]
        start = date(2026, 10, 12)
        for i in range(30):
            day = start + timedelta(days=i // 5)
            status = ("completed" if day < date(2026, 10, 16) else rng.choice(["planned", "confirmed", "cancelled"]))
            appointment = Appointment.objects.create(
                patient=rng.choice(patients), doctor=doctors[i % len(doctors)], date=day,
                time=time(9 + i % 5, 30 * (i % 2)), status=status, price=rng.choice([1200, 1500, 2000, 3500]),
                complaints=rng.choice(COMPLAINTS))
            if status == "completed":
                appointment.diagnoses.add(*rng.sample(diagnoses, k=rng.randint(1, 2)))
        admin = User.objects.create_superuser("admin", "admin@example.com", "admin12345")
        user = User.objects.create_user("user", "user@example.com", "user12345")
        user.user_permissions.add(Permission.objects.get(codename="view_appointment"))
        self.stdout.write(self.style.SUCCESS(f"Готово: 30 приёмов, пользователи {admin.username} и {user.username}"))
