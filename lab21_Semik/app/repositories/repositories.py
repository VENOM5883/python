"""Repository-слой: SQLAlchemy-запросы, без бизнес-правил."""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Customer, Order, Product, Stock, User, Warehouse

PRODUCT_SORTS = {"name": Product.name, "price": Product.price, "category": Product.category, "id": Product.id}


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def get(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def phone_taken(self, phone: str) -> bool:
        return self.session.scalar(select(Customer.id).where(Customer.phone == phone)) is not None

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, product_id: int) -> Product | None:
        return self.session.get(Product, product_id)

    def by_name(self, name: str) -> Product | None:
        # точное совпадение + регистронезависимое (lower() в SQLite не работает с кириллицей, в PostgreSQL — работает)
        return self.session.scalar(select(Product).where(
            or_(Product.name == name, func.lower(Product.name) == name.lower())).limit(1))

    def search(self, q: str | None, category: str | None, max_price, sort: str, order: str,
               skip: int, limit: int) -> tuple[list[Product], int]:
        stmt = select(Product)
        if q:
            stmt = stmt.where(or_(Product.name.ilike(f"%{q}%"), Product.manufacturer.ilike(f"%{q}%")))
        if category:
            stmt = stmt.where(Product.category == category)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        column = PRODUCT_SORTS[sort]
        stmt = stmt.order_by(column.desc() if order == "desc" else column.asc(), Product.id)
        return list(self.session.scalars(stmt.offset(skip).limit(limit))), total

    def available(self, product_id: int) -> int:
        return self.session.scalar(select(func.coalesce(func.sum(Stock.quantity), 0))
                                   .where(Stock.product_id == product_id))

    def has_orders(self, product_id: int) -> bool:
        from app.models import OrderItem
        return self.session.scalar(select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1)) is not None

    def add(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()
        return product

    def delete(self, product: Product) -> None:
        self.session.delete(product)


class WarehouseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def all(self) -> list[Warehouse]:
        return list(self.session.scalars(select(Warehouse).order_by(Warehouse.priority, Warehouse.id)))

    def get(self, warehouse_id: int) -> Warehouse | None:
        return self.session.get(Warehouse, warehouse_id)

    def add(self, warehouse: Warehouse) -> Warehouse:
        self.session.add(warehouse)
        self.session.flush()
        return warehouse

    def stock(self, product_id: int, warehouse_id: int) -> Stock | None:
        return self.session.scalar(select(Stock).where(Stock.product_id == product_id,
                                                       Stock.warehouse_id == warehouse_id))

    def stock_for_product(self, product_id: int) -> list[Stock]:
        """Остатки товара по складам в порядке приоритета списания (с блокировкой строк в PostgreSQL)."""
        stmt = (select(Stock).join(Warehouse).where(Stock.product_id == product_id, Stock.quantity > 0)
                .order_by(Warehouse.priority, Warehouse.id).with_for_update())
        return list(self.session.scalars(stmt))

    def add_stock(self, stock: Stock) -> Stock:
        self.session.add(stock)
        self.session.flush()
        return stock


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def list(self, customer_id: int | None, status: str | None) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc(), Order.id.desc())
        if customer_id is not None:
            stmt = stmt.where(Order.customer_id == customer_id)
        if status:
            stmt = stmt.where(Order.status == status)
        return list(self.session.scalars(stmt))

    def completed_total(self, customer_id: int):
        return self.session.scalar(select(func.coalesce(func.sum(Order.total), 0))
                                   .where(Order.customer_id == customer_id, Order.status == "completed"))

    def add(self, order: Order) -> Order:
        self.session.add(order)
        self.session.flush()
        return order
