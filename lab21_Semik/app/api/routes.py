from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import admin_user, current_user, get_db
from app.models import User
from app.schemas import (
    LoginIn,
    OrderIn,
    OrderOut,
    ProductIn,
    ProductOut,
    ProductPatch,
    ProfileOut,
    RegisterIn,
    StatusIn,
    StockIn,
    StockOut,
    TokenOut,
    WarehouseIn,
    WarehouseOut,
)
from app.services.services import AuthService, CatalogService, OrderService

ERRORS = {400: {"description": "Некорректные данные"}, 401: {"description": "Нет токена"},
          403: {"description": "Недостаточно прав"}, 404: {"description": "Не найдено"},
          409: {"description": "Нарушение бизнес-правила"}}

auth = APIRouter(prefix="/auth", tags=["Авторизация"])
products = APIRouter(prefix="/products", tags=["Каталог"])
warehouses = APIRouter(prefix="/warehouses", tags=["Склады"], dependencies=[Depends(admin_user)])
orders = APIRouter(prefix="/orders", tags=["Заказы"])


@auth.post("/register", response_model=ProfileOut, status_code=201, responses=ERRORS, summary="Регистрация покупателя")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    user = AuthService(db).register(data.email, data.password, data.full_name, data.phone)
    return ProfileOut(id=user.id, email=user.email, role=user.role, full_name=user.customer.full_name,
                      phone=user.customer.phone)


@auth.post("/login", response_model=TokenOut, responses=ERRORS, summary="Вход, получение JWT")
def login(data: LoginIn, db: Session = Depends(get_db)):
    token, role = AuthService(db).login(data.email, data.password)
    return TokenOut(access_token=token, role=role)


@auth.get("/profile", response_model=ProfileOut, responses=ERRORS, summary="Текущий пользователь")
def profile(user: User = Depends(current_user)):
    customer = user.customer
    return ProfileOut(id=user.id, email=user.email, role=user.role,
                      full_name=customer.full_name if customer else None, phone=customer.phone if customer else None)


@products.get("", response_model=dict, summary="Поиск, фильтрация, сортировка и пагинация каталога")
def list_products(q: str | None = Query(None, min_length=2), category: str | None = None,
                  max_price: Decimal | None = Query(None, gt=0), sort: str = "name",
                  order: str = Query("asc", pattern="^(asc|desc)$"), skip: int = Query(0, ge=0),
                  limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    items, total = CatalogService(db).search(q, category, max_price, sort, order, skip, limit)
    return {"items": [ProductOut.model_validate(p).model_dump(mode="json") for p in items],
            "total": total, "skip": skip, "limit": limit}


@products.get("/{product_id}", response_model=ProductOut, responses=ERRORS)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return CatalogService(db).get(product_id)


@products.post("", response_model=ProductOut, status_code=201, responses=ERRORS, dependencies=[Depends(admin_user)])
def create_product(data: ProductIn, db: Session = Depends(get_db)):
    return CatalogService(db).create(data.model_dump())


@products.put("/{product_id}", response_model=ProductOut, responses=ERRORS, dependencies=[Depends(admin_user)])
def replace_product(product_id: int, data: ProductIn, db: Session = Depends(get_db)):
    return CatalogService(db).update(product_id, data.model_dump())


@products.patch("/{product_id}", response_model=ProductOut, responses=ERRORS, dependencies=[Depends(admin_user)])
def patch_product(product_id: int, data: ProductPatch, db: Session = Depends(get_db)):
    return CatalogService(db).update(product_id, data.model_dump(exclude_unset=True, exclude_none=True))


@products.delete("/{product_id}", status_code=204, responses=ERRORS, dependencies=[Depends(admin_user)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    CatalogService(db).delete(product_id)
    return Response(status_code=204)


@warehouses.get("", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return CatalogService(db).warehouses.all()


@warehouses.post("", response_model=WarehouseOut, status_code=201, responses=ERRORS)
def create_warehouse(data: WarehouseIn, db: Session = Depends(get_db)):
    return CatalogService(db).create_warehouse(data.model_dump())


@warehouses.put("/stock", response_model=StockOut, responses=ERRORS, summary="Установить остаток товара на складе")
def set_stock(data: StockIn, db: Session = Depends(get_db)):
    return CatalogService(db).set_stock(data.product_id, data.warehouse_id, data.quantity)


@orders.post("", response_model=OrderOut, status_code=201, responses=ERRORS, summary="Оформить заказ")
def create_order(data: OrderIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return OrderService(db).create(user, [i.model_dump() for i in data.items], data.has_prescription)


@orders.get("", response_model=list[OrderOut], responses=ERRORS)
def list_orders(status: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return OrderService(db).list(user, status)


@orders.get("/statistics", dependencies=[Depends(admin_user)], summary="Статистика продаж (ADMIN)")
def statistics(db: Session = Depends(get_db)):
    return OrderService(db).statistics()


@orders.get("/{order_id}", response_model=OrderOut, responses=ERRORS)
def get_order(order_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return OrderService(db).get(user, order_id)


@orders.patch("/{order_id}/status", response_model=OrderOut, responses=ERRORS, summary="Изменить статус заказа")
def change_status(order_id: int, data: StatusIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return OrderService(db).change_status(user, order_id, data.status)
