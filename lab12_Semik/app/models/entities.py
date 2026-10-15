"""ORM-модели аптеки: Customer, Medicine, Purchase (+ PurchaseItem для N:M)."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    discount_card: Mapped[bool] = mapped_column(default=False)
    registered_at: Mapped[datetime] = mapped_column(server_default=func.now())

    purchases: Mapped[list["Purchase"]] = relationship(back_populates="customer",
                                                       cascade="all, delete-orphan")

    def __repr__(self) -> str:
        card = ", карта" if self.discount_card else ""
        return f"<Customer #{self.id} {self.full_name} {self.phone}{card}>"


class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = (
        UniqueConstraint("name", "form", name="uq_medicine_name_form"),
        CheckConstraint("price > 0", name="ck_medicine_price"),
        CheckConstraint("quantity >= 0", name="ck_medicine_quantity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    manufacturer: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))
    form: Mapped[str] = mapped_column(String(40))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(default=0)
    prescription_required: Mapped[bool] = mapped_column(default=False)

    items: Mapped[list["PurchaseItem"]] = relationship(back_populates="medicine", passive_deletes="all")

    def __repr__(self) -> str:
        rx = " (рецепт)" if self.prescription_required else ""
        return (f"<Medicine #{self.id} {self.name} {self.form}, {self.manufacturer}, "
                f"{self.category}, {self.price} руб., остаток {self.quantity}{rx}>")


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    customer: Mapped["Customer"] = relationship(back_populates="purchases")
    items: Mapped[list["PurchaseItem"]] = relationship(back_populates="purchase",
                                                       cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Purchase #{self.id} {self.created_at:%d.%m.%Y %H:%M} на {self.total} руб.>"


class PurchaseItem(Base):
    """Промежуточная таблица N:M «покупка — лекарство» с количеством и ценой."""
    __tablename__ = "purchase_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_item_quantity"),)

    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id", ondelete="CASCADE"),
                                             primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="RESTRICT"),
                                             primary_key=True)
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    purchase: Mapped["Purchase"] = relationship(back_populates="items")
    medicine: Mapped["Medicine"] = relationship(back_populates="items")
