"""Order Service — заказы (собственная БД orders).
Синхронно обращается к Product Service (цены) и Warehouse Service (резерв) через Retry + Circuit Breaker,
асинхронно публикует событие OrderCreated / OrderCancelled в брокер.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, Numeric, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload

from common import observability
from common.broker import create_broker
from common.db import make_session_factory
from common.resilience import CircuitBreaker, ResilientClient, ServiceUnavailableError


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(12), default="created")  # created / cancelled / completed
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    items: Mapped[list[OrderItem]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int]
    name: Mapped[str] = mapped_column(String(120))  # копия данных Product Service на момент заказа
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int]


class ItemIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class OrderIn(BaseModel):
    customer: str = Field(min_length=2, max_length=150)
    items: list[ItemIn] = Field(min_length=1)
    has_prescription: bool = False


class StatusIn(BaseModel):
    status: str = Field(pattern="^(cancelled|completed)$")


def order_dict(order: Order) -> dict:
    return {"id": order.id, "customer": order.customer, "status": order.status, "total": float(order.total),
            "created_at": order.created_at.isoformat(),
            "items": [{"product_id": i.product_id, "name": i.name, "price": float(i.price), "quantity": i.quantity}
                      for i in order.items]}


class OrderService:
    def __init__(self, session: Session, products: ResilientClient, warehouse: ResilientClient, broker) -> None:
        self.session = session
        self.products = products
        self.warehouse = warehouse
        self.broker = broker

    def get(self, order_id: str) -> Order:
        order = self.session.get(Order, order_id)
        if order is None:
            raise HTTPException(404, f"Order {order_id} not found")
        return order

    def _product(self, product_id: int) -> dict:
        response = self.products.request("GET", f"/products/{product_id}")
        if response.status_code == 404:
            raise HTTPException(400, f"Product {product_id} does not exist")
        return response.json()

    def create(self, data: OrderIn) -> Order:
        order_id = uuid.uuid4().hex[:12]
        products = {item.product_id: self._product(item.product_id) for item in data.items}
        for product in products.values():
            if product["prescription_required"] and not data.has_prescription:
                raise HTTPException(400, f"«{product['name']}» отпускается только по рецепту")
        # 1. резерв на складе
        response = self.warehouse.request("POST", "/reservations", json={
            "order_id": order_id, "items": [i.model_dump() for i in data.items]})
        if response.status_code == 409:
            raise HTTPException(409, response.json()["detail"])
        response.raise_for_status()
        # 2. сохранение заказа; при ошибке — компенсация (снятие резерва)
        try:
            order = Order(id=order_id, customer=data.customer, items=[
                OrderItem(product_id=i.product_id, name=products[i.product_id]["name"],
                          price=Decimal(str(products[i.product_id]["price"])), quantity=i.quantity)
                for i in data.items])
            order.total = sum(i.price * i.quantity for i in order.items)
            self.session.add(order)
            self.session.commit()
        except Exception:
            self.session.rollback()
            self.warehouse.request("DELETE", f"/reservations/{order_id}")
            raise
        # 3. асинхронное событие
        self.broker.publish("OrderCreated", order_dict(order))
        return order

    def change_status(self, order_id: str, status: str) -> Order:
        order = self.get(order_id)
        if order.status != "created":
            raise HTTPException(409, f"Order is already {order.status}")
        if status == "cancelled":
            self.warehouse.request("DELETE", f"/reservations/{order_id}")
        order.status = status
        self.session.commit()
        self.broker.publish("OrderCancelled" if status == "cancelled" else "OrderCompleted", order_dict(order))
        return order


def create_app(database_url: str | None = None, products: ResilientClient | None = None,
               warehouse: ResilientClient | None = None, broker=None) -> FastAPI:
    engine, SessionLocal = make_session_factory(database_url or os.getenv("DATABASE_URL", "sqlite:///./orders.db"))
    Base.metadata.create_all(engine)
    products = products or ResilientClient("product-service", os.getenv("PRODUCT_URL", "http://127.0.0.1:8001"),
                                           breaker=CircuitBreaker("product-service", 3, 10))
    warehouse = warehouse or ResilientClient("warehouse-service", os.getenv("WAREHOUSE_URL", "http://127.0.0.1:8002"),
                                             breaker=CircuitBreaker("warehouse-service", 3, 10))
    broker = broker or create_broker()

    app = FastAPI(title="Order Service")
    observability.setup(app, "order-service")

    @app.exception_handler(ServiceUnavailableError)
    async def unavailable(_, error: ServiceUnavailableError):
        return JSONResponse(status_code=503, content={"detail": str(error)})

    def service():
        with SessionLocal() as session:
            yield OrderService(session, products, warehouse, broker)

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "order-service",
                "circuit_breakers": [products.breaker.status(), warehouse.breaker.status()]}

    @app.get("/orders")
    def list_orders(svc: OrderService = Depends(service)):
        stmt = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
        return [order_dict(o) for o in svc.session.scalars(stmt)]

    @app.get("/orders/{order_id}")
    def get_order(order_id: str, svc: OrderService = Depends(service)):
        return order_dict(svc.get(order_id))

    @app.post("/orders", status_code=201)
    def create_order(data: OrderIn, svc: OrderService = Depends(service)):
        return order_dict(svc.create(data))

    @app.put("/orders/{order_id}")
    def update_order(order_id: str, data: StatusIn, svc: OrderService = Depends(service)):
        return order_dict(svc.change_status(order_id, data.status))

    @app.delete("/orders/{order_id}", status_code=204)
    def delete_order(order_id: str, svc: OrderService = Depends(service)):
        order = svc.get(order_id)
        if order.status == "created":
            raise HTTPException(409, "Cancel the order before deleting")
        svc.session.delete(order)
        svc.session.commit()
        return Response(status_code=204)

    return app


app = create_app() if os.getenv("SERVICE_AUTOSTART", "1") == "1" else None
