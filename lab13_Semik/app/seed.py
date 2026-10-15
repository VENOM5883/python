"""Генерация 24 учебных документов (вымышленные данные)."""
import random

from app.models import Appointment

DOCTORS = [
    {"id": 1, "full_name": "Смирнова Елена Викторовна", "specialty": "терапевт", "cabinet": 101},
    {"id": 2, "full_name": "Кузнецов Олег Петрович", "specialty": "кардиолог", "cabinet": 205},
    {"id": 3, "full_name": "Орлова Наталья Андреевна", "specialty": "невролог", "cabinet": 310},
    {"id": 4, "full_name": "Белова Мария Игоревна", "specialty": "окулист", "cabinet": 120},
]
PATIENTS = [("Иванов Иван Иванович", 1985), ("Петрова Анна Сергеевна", 1992),
            ("Сидоров Павел Олегович", 1970), ("Новикова Ольга Дмитриевна", 2001),
            ("Фёдоров Максим Ильич", 1965), ("Ковалёва Дарья Павловна", 1998)]
DIAGNOSES = {"терапевт": ("ОРВИ", ["Парацетамол", "Обильное питьё"]),
             "кардиолог": ("Гипертония I ст.", ["Лизиноприл", "ЭКГ через месяц"]),
             "невролог": ("Мигрень", ["Ибупрофен", "МРТ головного мозга"]),
             "окулист": ("Миопия", ["Капли Таурин", "Очки -1.5"])}


def generate(count: int = 24, seed: int = 15) -> list[dict]:
    rng = random.Random(seed)
    documents = []
    for i in range(count):
        doctor = DOCTORS[i % len(DOCTORS)]
        name, year = PATIENTS[rng.randrange(len(PATIENTS))]
        day = 20 + i // 8
        time = f"{9 + (i % 8) // 2:02d}:{30 * (i % 2):02d}"
        status = ("completed", "confirmed", "planned", "cancelled")[rng.randrange(4)] if day == 20 \
            else ("planned", "confirmed")[i % 2]
        diagnosis, prescriptions = DIAGNOSES[doctor["specialty"]] if status == "completed" else ("", [])
        documents.append(Appointment(
            patient={"full_name": name, "birth_year": year, "phone": f"+7900{1000000 + i:07d}"},
            doctor=dict(doctor), specialty=doctor["specialty"], date=f"2026-10-{day}", time=time,
            status=status, diagnosis=diagnosis, prescriptions=list(prescriptions)).to_document())
    return documents
