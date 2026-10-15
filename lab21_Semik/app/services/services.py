"""Сервисный слой: бизнес-правила аптеки.

Правила:
1. Нельзя заказать больше, чем есть на всех складах; списание идёт со складов по приоритету.
2. Рецептурный препарат отпускается только при наличии рецепта.
3. Переходы статусов заказа: created → paid → completed; отмена возможна из created/paid,
   при отмене товар возвращается на те же склады.
4. Скидка постоянного клиента 5 %, если сумма завершённых заказов ≥ 5000 руб.
5. Нельзя удалить препарат, который уже заказывали.
6. Пользователь видит и меняет только свои заказы (кроме ADMIN).
"""
from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import AuthError, BusinessRuleError, EntityNotFoundError, ForbiddenError, ValidationAppError
from app.models import Customer, Order, OrderItem, Product, Stock, User, Warehouse
from app.repositories.repositories import (
    PRODUCT_SORTS,
    OrderRepository,
    ProductRepository,
    UserRepository,
    WarehouseRepository,
)
from app.security import create_token, hash_password, verify_password

log = logging.getLogger("pharmacy")
LOYALTY_THRESHOLD = Decimal("5000")
LOYALTY_DISCOUNT = Decimal("0.05")
TRANSITIONS = {"created": {"paid", "cancelled"}, "paid": {"completed", "cancelled"},
               "completed": set(), "cancelled": set()}


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def register(self, email: str, password: str, full_name: str, phone: str, role: str = "USER") -> User:
        if self.users.by_email(email):
            raise BusinessRuleError("User with this email already exists", "EMAIL_TAKEN")
        if self.users.phone_taken(phone):
            raise BusinessRuleError("Phone already registered", "PHONE_TAKEN")
        user = self.users.add(User(email=email, password_hash=hash_password(password), role=role))
        user.customer = Customer(full_name=full_name, phone=phone)
        self.session.commit()
        log.info("User registered: %s (%s)", email, role)
        return user

    def login(self, email: str, password: str) -> tuple[str, str]:
        user = self.users.by_email(email.lower())
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password")
        return create_token(user.id, user.role), user.role


class CatalogService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.products = ProductRepository(session)
        self.warehouses = WarehouseRepository(session)

    def _with_availability(self, product: Product) -> Product:
        product.available = self.products.available(product.id)
        return product

    def search(self, q=None, category=None, max_price=None, sort="name", order="asc", skip=0, limit=20):
        if sort not in PRODUCT_SORTS:
            raise ValidationAppError(f"sort must be one of: {', '.join(PRODUCT_SORTS)}")
        items, total = self.products.search(q, category, max_price, sort, order, skip, limit)
        return [self._with_availability(p) for p in items], total

    def get(self, product_id: int) -> Product:
        product = self.products.get(product_id)
        if product is None:
            raise EntityNotFoundError(f"Product with id {product_id} not found", "PRODUCT_NOT_FOUND")
        return self._with_availability(product)

    @staticmethod
    def _normalize(data: dict) -> dict:
        if data.get("price") is not None:
            data["price"] = Decimal(data["price"]).quantize(Decimal("0.01"))
        return data

    def create(self, data: dict) -> Product:
        data = self._normalize(data)
        if self.products.by_name(data["name"]):
            raise BusinessRuleError(f"Product «{data['name']}» already exists", "PRODUCT_EXISTS")
        try:
            product = self.products.add(Product(**data))
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise BusinessRuleError(f"Product «{data['name']}» already exists", "PRODUCT_EXISTS") from None
        log.info("Product created: %s", product.name)
        return self._with_availability(product)

    def update(self, product_id: int, data: dict) -> Product:
        product = self.get(product_id)
        if not data:
            raise ValidationAppError("No fields to update")
        data = self._normalize(data)
        if "name" in data and data["name"].lower() != product.name.lower() and self.products.by_name(data["name"]):
            raise BusinessRuleError(f"Product «{data['name']}» already exists", "PRODUCT_EXISTS")
        for key, value in data.items():
            setattr(product, key, value)
        self.session.commit()
        return self._with_availability(product)

    def delete(self, product_id: int) -> None:
        product = self.get(product_id)
        if self.products.has_orders(product_id):                       # правило 5
            raise BusinessRuleError("Product was ordered and cannot be deleted", "PRODUCT_IN_ORDERS")
        self.products.delete(product)
        self.session.commit()
        log.info("Product deleted: %s", product_id)

    def create_warehouse(self, data: dict) -> Warehouse:
        warehouse = self.warehouses.add(Warehouse(**data))
        self.session.commit()
        return warehouse

    def set_stock(self, product_id: int, warehouse_id: int, quantity: int) -> Stock:
        self.get(product_id)
        if self.warehouses.get(warehouse_id) is None:
            raise EntityNotFoundError(f"Warehouse with id {warehouse_id} not found", "WAREHOUSE_NOT_FOUND")
        stock = self.warehouses.stock(product_id, warehouse_id)
        if stock is None:
            stock = self.warehouses.add_stock(Stock(product_id=product_id, warehouse_id=warehouse_id, quantity=0))
        stock.quantity = quantity
        self.session.commit()
        log.info("Stock set: product %s, warehouse %s -> %s", product_id, warehouse_id, quantity)
        return stock


class OrderService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.orders = OrderRepository(session)
        self.products = ProductRepository(session)
        self.warehouses = WarehouseRepository(session)

    @staticmethod
    def _customer(user: User) -> Customer:
        if user.customer is None:
            raise BusinessRuleError("User has no customer profile", "NO_CUSTOMER_PROFILE")
        return user.customer

    def create(self, user: User, items: list[dict], has_prescription: bool) -> Order:
        customer = self._customer(user)
        try:
            order = Order(customer_id=customer.id, subtotal=Decimal(0), discount=Decimal("0.00"), total=Decimal(0))
            subtotal = Decimal(0)
            for item in items:
                product = self.products.get(item["product_id"])
                if product is None:
                    raise EntityNotFoundError(f"Product with id {item['product_id']} not found", "PRODUCT_NOT_FOUND")
                if product.prescription_required and not has_prescription:      # правило 2
                    raise BusinessRuleError(f"«{product.name}» requires a prescription", "PRESCRIPTION_REQUIRED")
                need = item["quantity"]
                stocks = self.warehouses.stock_for_product(product.id)
                available = sum(s.quantity for s in stocks)
                if available < need:                                             # правило 1
                    raise BusinessRuleError(f"Not enough «{product.name}»: available {available}, requested {need}",
                                            "OUT_OF_STOCK")
                for stock in stocks:                                             # списание по приоритету складов
                    take = min(stock.quantity, need)
                    if take == 0:
                        continue
                    stock.quantity -= take
                    order.items.append(OrderItem(product_id=product.id, warehouse_id=stock.warehouse_id,
                                                 quantity=take, price=product.price))
                    need -= take
                    if need == 0:
                        break
                subtotal += product.price * item["quantity"]
            if self.orders.completed_total(customer.id) >= LOYALTY_THRESHOLD:       # правило 4
                order.discount = (subtotal * LOYALTY_DISCOUNT).quantize(Decimal("0.01"))
            order.subtotal, order.total = subtotal, subtotal - order.discount
            self.orders.add(order)
            self.session.commit()                                                # одна транзакция
        except Exception:
            self.session.rollback()
            raise
        log.info("Order %s created by %s, total %s", order.id, user.email, order.total)
        return order

    def get(self, user: User, order_id: int) -> Order:
        order = self.orders.get(order_id)
        if order is None:
            raise EntityNotFoundError(f"Order with id {order_id} not found", "ORDER_NOT_FOUND")
        if user.role != "ADMIN" and (user.customer is None or order.customer_id != user.customer.id):  # правило 6
            raise ForbiddenError("You can access only your own orders")
        return order

    def list(self, user: User, status: str | None = None) -> list[Order]:
        customer_id = None if user.role == "ADMIN" else self._customer(user).id
        return self.orders.list(customer_id, status)

    def change_status(self, user: User, order_id: int, status: str) -> Order:
        order = self.get(user, order_id)
        if status == "completed" and user.role != "ADMIN":
            raise ForbiddenError("Only administrator can complete orders")
        if status not in TRANSITIONS[order.status]:                               # правило 3
            raise BusinessRuleError(f"Cannot change status from {order.status} to {status}", "INVALID_TRANSITION")
        if status == "cancelled":
            for item in order.items:
                self.warehouses.stock(item.product_id, item.warehouse_id).quantity += item.quantity
        order.status = status
        self.session.commit()
        log.info("Order %s -> %s by %s", order.id, status, user.email)
        return order

    def statistics(self) -> dict:
        orders = self.orders.list(None, None)
        done = [o for o in orders if o.status == "completed"]
        return {"orders": len(orders), "completed": len(done),
                "revenue": float(sum((o.total for o in done), Decimal(0))),
                "by_status": {s: sum(1 for o in orders if o.status == s) for s in TRANSITIONS}}
