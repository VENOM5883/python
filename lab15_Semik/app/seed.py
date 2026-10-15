from decimal import Decimal

from sqlalchemy import select

from app.models.models import Category, Medicine

CATEGORIES = [("Обезболивающие", "Анальгетики и НПВС"), ("Антибиотики", "Отпуск по рецепту"),
              ("Витамины", "Витаминные комплексы"), ("Противоаллергические", "Антигистаминные"),
              ("ЖКТ", "Средства для пищеварения")]
MEDICINES = [
    ("Парацетамол", "Фармстандарт", "таблетки", "45", 120, False, 1),
    ("Ибупрофен", "Борисовский ЗМП", "таблетки", "89", 80, False, 1),
    ("Нурофен", "Reckitt", "сироп", "320", 25, False, 1),
    ("Амоксициллин", "Хемофарм", "капсулы", "210", 40, True, 2),
    ("Азитромицин", "Вертекс", "таблетки", "260", 0, True, 2),
    ("Витамин D3", "Аквадетрим", "капли", "310", 35, False, 3),
    ("Аскорбиновая кислота", "Марбиофарм", "драже", "38", 200, False, 3),
    ("Лоратадин", "Озон", "таблетки", "95", 60, False, 4),
    ("Цетиризин", "Teva", "капли", "240", 12, False, 4),
    ("Омепразол", "Озон", "капсулы", "120", 50, False, 5),
]


def seed(session) -> None:
    if session.scalar(select(Category.id).limit(1)) is not None:
        return
    session.add_all(Category(name=n, description=d) for n, d in CATEGORIES)
    session.flush()
    session.add_all(Medicine(name=n, manufacturer=m, form=f, price=Decimal(p), quantity=q,
                             prescription_required=rx, category_id=c)
                    for n, m, f, p, q, rx, c in MEDICINES)
    session.commit()
