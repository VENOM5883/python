"""Тестовые данные."""
from app.services.services import PharmacyService

MEDICINES = [
    ("Парацетамол", "Фармстандарт", "жаропонижающие", "таблетки", 45, 120, False),
    ("Ибупрофен", "Борисовский ЗМП", "обезболивающие", "таблетки", 89, 80, False),
    ("Нурофен", "Reckitt", "обезболивающие", "сироп", 320, 25, False),
    ("Амоксициллин", "Хемофарм", "антибиотики", "капсулы", 210, 40, True),
    ("Азитромицин", "Вертекс", "антибиотики", "таблетки", 260, 15, True),
    ("Лоратадин", "Озон", "противоаллергические", "таблетки", 95, 60, False),
    ("Цетиризин", "Teva", "противоаллергические", "капли", 240, 0, False),
    ("Витамин D3", "Аквадетрим", "витамины", "капли", 310, 35, False),
    ("Аскорбиновая кислота", "Марбиофарм", "витамины", "драже", 38, 200, False),
    ("Омепразол", "Озон", "ЖКТ", "капсулы", 120, 50, False),
]


def seed(service: PharmacyService) -> None:
    if service.list_medicines():
        return
    for data in MEDICINES:
        service.add_medicine(*data)
    service.add_customer("Иванов Иван Иванович", "+79001112233", discount_card=True)
    service.add_customer("Петрова Анна Сергеевна", "+79002223344")
    service.add_customer("Сидоров Павел Олегович", "+79003334455")
    service.make_purchase(1, {1: 2, 6: 1})
    service.make_purchase(2, {4: 1}, has_prescription=True)
