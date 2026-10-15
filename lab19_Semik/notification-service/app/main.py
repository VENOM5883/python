"""Notification Service — потребитель событий брокера (OrderCreated и др.), хранит уведомления в своей БД."""
from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from common import observability
from common.broker import create_broker
from common.db import make_session_factory

log = logging.getLogger("notification-service")


class Base(DeclarativeBase):
    pass


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(40), unique=True)  # идемпотентность обработки
    event_type: Mapped[str] = mapped_column(String(40))
    recipient: Mapped[str] = mapped_column(String(150))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


TEMPLATES = {
    "OrderCreated": lambda p: (p["customer"], f"Заказ {p['id']} на {p['total']:.2f} руб. оформлен, товар зарезервирован"),
    "OrderCancelled": lambda p: (p["customer"], f"Заказ {p['id']} отменён, резерв снят"),
    "OrderCompleted": lambda p: (p["customer"], f"Заказ {p['id']} выдан. Будьте здоровы!"),
    "StockReceived": lambda p: ("склад", f"Поступление товара {p['product_id']}: +{p['received']} шт."),
    "ProductReserved": lambda p: ("склад", f"Резерв по заказу {p['order_id']}: {len(p['items'])} поз."),
}


class NotificationHandler:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    def __call__(self, event: dict) -> Notification | None:
        template = TEMPLATES.get(event["type"])
        if template is None:
            return None
        recipient, text = template(event["payload"])
        with self.session_factory() as session:
            if session.scalar(select(Notification.id).where(Notification.event_id == event["event_id"])):
                return None  # повторная доставка
            notification = Notification(event_id=event["event_id"], event_type=event["type"],
                                        recipient=recipient, text=text)
            session.add(notification)
            session.commit()
        log.info("Событие %s получено -> уведомление «%s»: %s", event["type"], recipient, text)
        return notification


def create_app(database_url: str | None = None, broker=None, start_consumer: bool = True) -> FastAPI:
    engine, SessionLocal = make_session_factory(
        database_url or os.getenv("DATABASE_URL", "sqlite:///./notifications.db"))
    Base.metadata.create_all(engine)
    handler = NotificationHandler(SessionLocal)
    stop = threading.Event()

    @asynccontextmanager
    async def lifespan(_):
        if start_consumer:
            consumer = broker or create_broker()
            threading.Thread(target=consumer.consume, kwargs={"handler": handler, "stop": stop}, daemon=True).start()
        yield
        stop.set()

    app = FastAPI(title="Notification Service", lifespan=lifespan)
    observability.setup(app, "notification-service")
    app.state.handler = handler

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "notification-service"}

    @app.get("/notifications")
    def list_notifications(recipient: str | None = None):
        with SessionLocal() as session:
            stmt = select(Notification).order_by(Notification.id.desc())
            if recipient:
                stmt = stmt.where(Notification.recipient == recipient)
            return [{"id": n.id, "type": n.event_type, "recipient": n.recipient, "text": n.text,
                     "created_at": n.created_at.isoformat()} for n in session.scalars(stmt)]

    return app


app = create_app() if os.getenv("SERVICE_AUTOSTART", "1") == "1" else None
