"""Модель данных: User, Customer, Product, Warehouse, Stock (товар на складе), Order, OrderItem."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(10), default="USER")  # USER / ADMIN
    customer: Mapped[Customer | None] = relationship(back_populates="user", uselist=False)


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(16), unique=True)
    user: Mapped[User] = relationship(back_populates="customer")
    orders: Mapped[list[Order]] = relationship(back_populates="customer")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price > 0", name="ck_product_price"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    manufacturer: Mapped[str] = mapped_column(String(120))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    prescription_required: Mapped[bool] = mapped_column(default=False)
    stock: Mapped[list[Stock]] = relationship(back_populates="product", cascade="all, delete-orphan")


class Warehouse(Base):
    __tablename__ = "warehouses"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    address: Mapped[str] = mapped_column(String(200))
    priority: Mapped[int] = mapped_column(default=1)  # с какого склада списывать в первую очередь
    stock: Mapped[list[Stock]] = relationship(back_populates="warehouse")


class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (UniqueConstraint("product_id", "warehouse_id"),
                      CheckConstraint("quantity >= 0", name="ck_stock_quantity"))
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(default=0)
    product: Mapped[Product] = relationship(back_populates="stock")
    warehouse: Mapped[Warehouse] = relationship(back_populates="stock")


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(String(12), default="created")  # created/paid/completed/cancelled
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    customer: Mapped[Customer] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order", cascade="all, delete-orphan",
                                                  lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_item_quantity"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"))
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(lazy="joined")
