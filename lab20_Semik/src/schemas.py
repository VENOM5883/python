from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MedicineIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    quantity: int = Field(ge=0)


class MedicineOut(MedicineIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SaleIn(BaseModel):
    medicine_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    medicine_id: int
    quantity: int
    total: Decimal
