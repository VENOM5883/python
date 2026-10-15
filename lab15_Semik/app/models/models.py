"""ORM-модели: Category 1:N Medicine, Purchase N:M Medicine (через PurchaseItem)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    medicines: Mapped[list["Medicine"]] = relationship(back_populates="category")


class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = (CheckConstraint("price > 0"), CheckConstraint("quantity >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    manufacturer: Mapped[str] = mapped_column(String(120))
    form: Mapped[str] = mapped_column(String(40))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(default=0)
    prescription_required: Mapped[bool] = mapped_column(default=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    category: Mapped["Category"] = relationship(back_populates="medicines")
    items: Mapped[list["PurchaseItem"]] = relationship(back_populates="medicine", passive_deletes="all")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "manufacturer": self.manufacturer, "form": self.form,
                "price": float(self.price), "quantity": self.quantity,
                "prescription_required": self.prescription_required,
                "category_id": self.category_id, "category": self.category.name if self.category else None}


class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    items: Mapped[list["PurchaseItem"]] = relationship(back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"), primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="RESTRICT"), primary_key=True)
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    purchase: Mapped["Purchase"] = relationship(back_populates="items")
    medicine: Mapped["Medicine"] = relationship(back_populates="items")
