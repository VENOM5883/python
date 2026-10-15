from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)


class RegisterIn(BaseModel):
    email: str = Field(max_length=120)
    password: str = Field(min_length=8, max_length=64)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(pattern=r"^\+7\d{10}$")

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        if not EMAIL_RE.match(value):
            raise ValueError("invalid email")
        return value.lower()


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class ProfileOut(BaseModel):
    id: int
    email: str
    role: str
    full_name: str | None
    phone: str | None


class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    manufacturer: str = Field(min_length=2, max_length=120)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    prescription_required: bool = False


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    category: str | None = Field(default=None, min_length=2, max_length=60)
    manufacturer: str | None = Field(default=None, min_length=2, max_length=120)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    prescription_required: bool | None = None


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    available: int = 0


class WarehouseIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=5, max_length=200)
    priority: int = Field(default=1, ge=1, le=10)


class WarehouseOut(WarehouseIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StockIn(BaseModel):
    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    quantity: int = Field(ge=0, le=100_000)


class StockOut(StockIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderItemIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=50)


class OrderIn(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=20)
    has_prescription: bool = False

    @field_validator("items")
    @classmethod
    def unique_products(cls, items: list[OrderItemIn]) -> list[OrderItemIn]:
        ids = [i.product_id for i in items]
        if len(ids) != len(set(ids)):
            raise ValueError("each product may appear only once")
        return items


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    warehouse_id: int
    quantity: int
    price: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    status: str
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    created_at: datetime
    items: list[OrderItemOut]


class StatusIn(BaseModel):
    status: Literal["paid", "completed", "cancelled"]
