"""Бизнес-логика: каталог и продажа с контролем остатка."""
from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models import Medicine, Sale

log = logging.getLogger("pharmacy")


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class PharmacyService:
    def __init__(self, session) -> None:
        self.session = session

    def list(self, category: str | None = None) -> list[Medicine]:
        stmt = select(Medicine).order_by(Medicine.name)
        if category:
            stmt = stmt.where(Medicine.category == category)
        return list(self.session.scalars(stmt))

    def get(self, medicine_id: int) -> Medicine:
        medicine = self.session.get(Medicine, medicine_id)
        if medicine is None:
            raise NotFoundError(f"Medicine {medicine_id} not found")
        return medicine

    def create(self, data: dict) -> Medicine:
        medicine = Medicine(**data)
        self.session.add(medicine)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise ConflictError(f"Medicine «{data['name']}» already exists") from None
        log.info("Medicine created: %s", medicine.name)
        return medicine

    def update(self, medicine_id: int, data: dict) -> Medicine:
        medicine = self.get(medicine_id)
        for key, value in data.items():
            setattr(medicine, key, value)
        self.session.commit()
        return medicine

    def delete(self, medicine_id: int) -> None:
        medicine = self.get(medicine_id)
        if self.session.scalar(select(Sale.id).where(Sale.medicine_id == medicine_id).limit(1)):
            raise ConflictError("Medicine has sales and cannot be deleted")
        self.session.delete(medicine)
        self.session.commit()

    def sell(self, medicine_id: int, quantity: int) -> Sale:
        medicine = self.get(medicine_id)
        if medicine.quantity < quantity:
            raise ConflictError(f"Not enough «{medicine.name}»: {medicine.quantity} left")
        medicine.quantity -= quantity
        sale = Sale(medicine_id=medicine.id, quantity=quantity, total=Decimal(medicine.price) * quantity)
        self.session.add(sale)
        self.session.commit()
        log.info("Sale: %s x%d = %s", medicine.name, quantity, sale.total)
        return sale
