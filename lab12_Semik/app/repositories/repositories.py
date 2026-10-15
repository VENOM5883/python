"""Repository-слой: доступ к данным только через SQLAlchemy ORM."""
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Customer, Medicine, Purchase

MEDICINE_SORTS = {
    "price": Medicine.price.asc(),
    "-price": Medicine.price.desc(),
    "name": Medicine.name.asc(),
    "quantity": Medicine.quantity.asc(),
}


class MedicineRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **fields) -> Medicine:
        medicine = Medicine(**fields)
        self.session.add(medicine)
        self.session.flush()
        return medicine

    def get_by_id(self, medicine_id: int) -> Medicine | None:
        return self.session.get(Medicine, medicine_id)

    def get_all(self, sort: str = "name", limit: int | None = None, offset: int = 0) -> list[Medicine]:
        stmt = select(Medicine).order_by(MEDICINE_SORTS[sort]).offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def update(self, medicine: Medicine, **fields) -> Medicine:
        for key, value in fields.items():
            setattr(medicine, key, value)
        self.session.flush()
        return medicine

    def delete(self, medicine: Medicine) -> None:
        self.session.delete(medicine)
        self.session.flush()

    def search(self, text: str) -> list[Medicine]:
        pattern = f"%{text}%"
        stmt = select(Medicine).where(or_(Medicine.name.ilike(pattern),
                                          Medicine.manufacturer.ilike(pattern)))
        return list(self.session.scalars(stmt.order_by(Medicine.name)))

    def filter(self, category: str | None = None, max_price: Decimal | None = None,
               in_stock: bool = False, sort: str = "price") -> list[Medicine]:
        conditions = []
        if category:
            conditions.append(Medicine.category == category)
        if max_price is not None:
            conditions.append(Medicine.price <= max_price)
        if in_stock:
            conditions.append(Medicine.quantity > 0)
        stmt = select(Medicine).where(and_(*conditions)).order_by(MEDICINE_SORTS[sort])
        return list(self.session.scalars(stmt))

    def statistics(self) -> dict:
        row = self.session.execute(select(
            func.count(Medicine.id), func.sum(Medicine.price * Medicine.quantity),
            func.avg(Medicine.price), func.min(Medicine.price), func.max(Medicine.price))).one()
        return {"count": row[0], "stock_value": row[1], "avg_price": row[2],
                "min_price": row[3], "max_price": row[4]}


class CustomerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **fields) -> Customer:
        customer = Customer(**fields)
        self.session.add(customer)
        self.session.flush()
        return customer

    def get_by_id(self, customer_id: int) -> Customer | None:
        return self.session.get(Customer, customer_id)

    def get_all(self) -> list[Customer]:
        return list(self.session.scalars(select(Customer).order_by(Customer.full_name)))

    def purchases_of(self, customer_id: int) -> list[Purchase]:
        stmt = (select(Purchase).where(Purchase.customer_id == customer_id)
                .options(selectinload(Purchase.items)).order_by(Purchase.created_at.desc()))
        return list(self.session.scalars(stmt))


class PurchaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, purchase: Purchase) -> Purchase:
        self.session.add(purchase)
        self.session.flush()
        return purchase

    def get_by_id(self, purchase_id: int) -> Purchase | None:
        return self.session.get(Purchase, purchase_id)
