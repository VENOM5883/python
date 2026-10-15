"""Product Service — каталог лекарственных препаратов (собственная БД products)."""
from __future__ import annotations

import os
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Numeric, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from common import observability
from common.db import make_session_factory


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    manufacturer: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    prescription_required: Mapped[bool] = mapped_column(default=False)


class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    manufacturer: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    prescription_required: bool = False


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


SEED = [("Парацетамол", "Фармстандарт", "обезболивающие", "45.00", False),
        ("Ибупрофен", "Борисовский ЗМП", "обезболивающие", "89.00", False),
        ("Амоксициллин", "Хемофарм", "антибиотики", "210.00", True),
        ("Витамин D3", "Аквадетрим", "витамины", "310.00", False),
        ("Лоратадин", "Озон", "противоаллергические", "95.00", False)]


class ProductService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, category: str | None) -> list[Product]:
        stmt = select(Product).order_by(Product.id)
        if category:
            stmt = stmt.where(Product.category == category)
        return list(self.session.scalars(stmt))

    def get(self, product_id: int) -> Product:
        product = self.session.get(Product, product_id)
        if product is None:
            raise HTTPException(404, f"Product {product_id} not found")
        return product

    def save(self, product: Product) -> Product:
        try:
            self.session.add(product)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise HTTPException(409, "Product with this name already exists") from None
        return product


def create_app(database_url: str | None = None) -> FastAPI:
    engine, SessionLocal = make_session_factory(database_url or os.getenv("DATABASE_URL", "sqlite:///./products.db"))
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.scalar(select(Product.id).limit(1)) is None:
            session.add_all(Product(name=n, manufacturer=m, category=c, price=Decimal(p), prescription_required=r)
                            for n, m, c, p, r in SEED)
            session.commit()

    app = FastAPI(title="Product Service")
    observability.setup(app, "product-service")

    def service():
        with SessionLocal() as session:
            yield ProductService(session)

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "product-service"}

    @app.get("/products", response_model=list[ProductOut])
    def list_products(category: str | None = Query(None), svc: ProductService = Depends(service)):
        return svc.list(category)

    @app.get("/products/{product_id}", response_model=ProductOut)
    def get_product(product_id: int, svc: ProductService = Depends(service)):
        return svc.get(product_id)

    @app.post("/products", response_model=ProductOut, status_code=201)
    def create_product(data: ProductIn, svc: ProductService = Depends(service)):
        return svc.save(Product(**data.model_dump()))

    @app.put("/products/{product_id}", response_model=ProductOut)
    def update_product(product_id: int, data: ProductIn, svc: ProductService = Depends(service)):
        product = svc.get(product_id)
        for key, value in data.model_dump().items():
            setattr(product, key, value)
        return svc.save(product)

    @app.delete("/products/{product_id}", status_code=204)
    def delete_product(product_id: int, svc: ProductService = Depends(service)):
        svc.session.delete(svc.get(product_id))
        svc.session.commit()
        return Response(status_code=204)

    return app


app = create_app() if os.getenv("SERVICE_AUTOSTART", "1") == "1" else None
