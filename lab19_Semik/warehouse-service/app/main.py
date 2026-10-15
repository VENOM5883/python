"""Warehouse Service — остатки и резервирование товара (собственная БД warehouse)."""
from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, String, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from common import observability
from common.broker import create_broker
from common.db import make_session_factory


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stock"
    product_id: Mapped[int] = mapped_column(primary_key=True)  # id из Product Service (без FK между БД)
    quantity: Mapped[int] = mapped_column(default=0)
    reserved: Mapped[int] = mapped_column(default=0)


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("order_id", "product_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(40), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("stock.product_id"))
    quantity: Mapped[int]
    status: Mapped[str] = mapped_column(String(12), default="reserved")  # reserved / released


class StockIn(BaseModel):
    quantity: int = Field(ge=0)


class Item(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class ReservationIn(BaseModel):
    order_id: str = Field(min_length=1, max_length=40)
    items: list[Item] = Field(min_length=1)


def stock_dict(stock: Stock) -> dict:
    return {"product_id": stock.product_id, "quantity": stock.quantity, "reserved": stock.reserved,
            "available": stock.quantity - stock.reserved}


class WarehouseService:
    def __init__(self, session: Session, broker) -> None:
        self.session = session
        self.broker = broker

    def get(self, product_id: int) -> Stock:
        stock = self.session.get(Stock, product_id)
        if stock is None:
            raise HTTPException(404, f"No stock for product {product_id}")
        return stock

    def set_quantity(self, product_id: int, quantity: int) -> Stock:
        stock = self.session.get(Stock, product_id) or Stock(product_id=product_id, reserved=0)
        if quantity < (stock.reserved or 0):
            raise HTTPException(409, "Quantity cannot be less than reserved amount")
        received = quantity - (stock.quantity or 0)
        stock.quantity = quantity
        self.session.add(stock)
        self.session.commit()
        if received > 0:
            self.broker.publish("StockReceived", {"product_id": product_id, "received": received})
        return stock

    def reserve(self, data: ReservationIn) -> list[dict]:
        """Резерв всех позиций в одной транзакции: либо всё, либо ничего."""
        if self.session.scalar(select(Reservation.id).where(Reservation.order_id == data.order_id).limit(1)):
            raise HTTPException(409, f"Order {data.order_id} already has reservation")
        try:
            for item in data.items:
                stock = self.session.get(Stock, item.product_id)
                available = (stock.quantity - stock.reserved) if stock else 0
                if available < item.quantity:
                    raise HTTPException(409, f"Not enough product {item.product_id}: available {available}")
                stock.reserved += item.quantity
                self.session.add(Reservation(order_id=data.order_id, product_id=item.product_id,
                                             quantity=item.quantity))
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.broker.publish("ProductReserved", {"order_id": data.order_id,
                                                "items": [i.model_dump() for i in data.items]})
        return [stock_dict(self.get(i.product_id)) for i in data.items]

    def release(self, order_id: str) -> int:
        """Компенсирующее действие: снять резерв заказа."""
        reservations = self.session.scalars(select(Reservation).where(
            Reservation.order_id == order_id, Reservation.status == "reserved")).all()
        if not reservations:
            raise HTTPException(404, f"No active reservation for order {order_id}")
        for reservation in reservations:
            self.session.get(Stock, reservation.product_id).reserved -= reservation.quantity
            reservation.status = "released"
        self.session.commit()
        return len(reservations)


def create_app(database_url: str | None = None, broker=None) -> FastAPI:
    engine, SessionLocal = make_session_factory(database_url or os.getenv("DATABASE_URL", "sqlite:///./warehouse.db"))
    Base.metadata.create_all(engine)
    broker = broker or create_broker()
    with SessionLocal() as session:
        if session.scalar(select(Stock.product_id).limit(1)) is None:
            session.add_all(Stock(product_id=pid, quantity=q, reserved=0)
                            for pid, q in [(1, 100), (2, 50), (3, 10), (4, 25), (5, 0)])
            session.commit()

    app = FastAPI(title="Warehouse Service")
    observability.setup(app, "warehouse-service")

    def service():
        with SessionLocal() as session:
            yield WarehouseService(session, broker)

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "warehouse-service"}

    @app.get("/stock")
    def list_stock(svc: WarehouseService = Depends(service)):
        return [stock_dict(s) for s in svc.session.scalars(select(Stock).order_by(Stock.product_id))]

    @app.get("/stock/{product_id}")
    def get_stock(product_id: int, svc: WarehouseService = Depends(service)):
        return stock_dict(svc.get(product_id))

    @app.put("/stock/{product_id}")
    def put_stock(product_id: int, data: StockIn, svc: WarehouseService = Depends(service)):
        return stock_dict(svc.set_quantity(product_id, data.quantity))

    @app.delete("/stock/{product_id}", status_code=204)
    def delete_stock(product_id: int, svc: WarehouseService = Depends(service)):
        stock = svc.get(product_id)
        if stock.reserved:
            raise HTTPException(409, "Product has active reservations")
        svc.session.delete(stock)
        svc.session.commit()
        return Response(status_code=204)

    @app.post("/reservations", status_code=201)
    def reserve(data: ReservationIn, svc: WarehouseService = Depends(service)):
        return {"order_id": data.order_id, "stock": svc.reserve(data)}

    @app.delete("/reservations/{order_id}")
    def release(order_id: str, svc: WarehouseService = Depends(service)):
        return {"order_id": order_id, "released_items": svc.release(order_id)}

    return app


app = create_app() if os.getenv("SERVICE_AUTOSTART", "1") == "1" else None
