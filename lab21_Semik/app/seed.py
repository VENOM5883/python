from decimal import Decimal

from sqlalchemy import select

from app.config import settings
from app.models import Product, Stock, User, Warehouse
from app.security import hash_password

PRODUCTS = [("Парацетамол", "обезболивающие", "Фармстандарт", "45.00", False),
            ("Ибупрофен", "обезболивающие", "Борисовский ЗМП", "89.00", False),
            ("Амоксициллин", "антибиотики", "Хемофарм", "210.00", True),
            ("Витамин D3", "витамины", "Аквадетрим", "310.00", False),
            ("Лоратадин", "противоаллергические", "Озон", "95.00", False),
            ("Омепразол", "ЖКТ", "Озон", "120.00", False)]
STOCK = {1: (60, 40), 2: (30, 0), 3: (10, 5), 4: (0, 20), 5: (25, 25), 6: (0, 0)}


def seed(session) -> None:
    if session.scalar(select(User.id).limit(1)) is not None:
        return
    session.add(User(email=settings.admin_email, password_hash=hash_password(settings.admin_password), role="ADMIN"))
    main = Warehouse(name="Центральный склад", address="г. Москва, ул. Складская, 1", priority=1)
    reserve = Warehouse(name="Резервный склад", address="г. Москва, ул. Промышленная, 7", priority=2)
    session.add_all([main, reserve])
    session.flush()
    for index, (name, category, manufacturer, price, rx) in enumerate(PRODUCTS, start=1):
        product = Product(name=name, category=category, manufacturer=manufacturer, price=Decimal(price),
                          prescription_required=rx)
        session.add(product)
        session.flush()
        first, second = STOCK[index]
        session.add_all([Stock(product_id=product.id, warehouse_id=main.id, quantity=first),
                         Stock(product_id=product.id, warehouse_id=reserve.id, quantity=second)])
    session.commit()
