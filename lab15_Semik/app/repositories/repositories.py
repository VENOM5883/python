from __future__ import annotations

from sqlalchemy import func, or_, select

from app.models.models import Category, Medicine, Purchase

SORTS = {"name": Medicine.name.asc(), "price": Medicine.price.asc(), "-price": Medicine.price.desc(),
         "quantity": Medicine.quantity.asc()}


class MedicineRepository:
    def __init__(self, session) -> None:
        self.session = session

    def list(self, search: str | None = None, category_id: int | None = None,
             in_stock: bool = False, prescription: str | None = None, sort: str = "name") -> list[Medicine]:
        stmt = select(Medicine)
        if search:
            stmt = stmt.where(or_(Medicine.name.ilike(f"%{search}%"),
                                  Medicine.manufacturer.ilike(f"%{search}%")))
        if category_id:
            stmt = stmt.where(Medicine.category_id == category_id)
        if in_stock:
            stmt = stmt.where(Medicine.quantity > 0)
        if prescription in ("yes", "no"):
            stmt = stmt.where(Medicine.prescription_required == (prescription == "yes"))
        return list(self.session.scalars(stmt.order_by(SORTS.get(sort, SORTS["name"]))))

    def get(self, medicine_id: int) -> Medicine | None:
        return self.session.get(Medicine, medicine_id)

    def add(self, medicine: Medicine) -> Medicine:
        self.session.add(medicine)  # INSERT выполнится при commit в сервисе
        return medicine

    def delete(self, medicine: Medicine) -> None:
        self.session.delete(medicine)
        self.session.flush()

    def count(self) -> int:
        return self.session.scalar(select(func.count(Medicine.id)))


class CategoryRepository:
    def __init__(self, session) -> None:
        self.session = session

    def list(self) -> list[Category]:
        return list(self.session.scalars(select(Category).order_by(Category.name)))

    def get(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def add(self, category: Category) -> Category:
        self.session.add(category)
        self.session.flush()
        return category


class PurchaseRepository:
    def __init__(self, session) -> None:
        self.session = session

    def add(self, purchase: Purchase) -> Purchase:
        self.session.add(purchase)
        self.session.flush()
        return purchase

    def get(self, purchase_id: int) -> Purchase | None:
        return self.session.get(Purchase, purchase_id)

    def list(self) -> list[Purchase]:
        return list(self.session.scalars(select(Purchase).order_by(Purchase.created_at.desc())))
