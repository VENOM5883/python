from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions import BusinessRuleError, EntityNotFoundError, ForbiddenError
from app.models import Customer, Order, OrderItem, Product, Stock, User
from app.services.services import OrderService


@pytest.fixture
def user():
    u = User(id=1, email="u@test.ru", role="USER")
    u.customer = Customer(id=10, full_name="Семик", phone="+79001234567")
    return u


@pytest.fixture
def service():
    with patch("app.services.services.ProductRepository") as products, \
         patch("app.services.services.WarehouseRepository") as warehouses, \
         patch("app.services.services.OrderRepository") as orders:
        svc = OrderService(MagicMock())
        svc.products, svc.warehouses, svc.orders = products.return_value, warehouses.return_value, orders.return_value
        svc.orders.completed_total.return_value = Decimal(0)
        svc.products.get.return_value = Product(id=1, name="Парацетамол", price=Decimal("45.00"),
                                                prescription_required=False)
        yield svc


def test_order_takes_stock_from_warehouses_by_priority(service, user):
    first, second = Stock(product_id=1, warehouse_id=1, quantity=3), Stock(product_id=1, warehouse_id=2, quantity=10)
    service.warehouses.stock_for_product.return_value = [first, second]
    order = service.create(user, [{"product_id": 1, "quantity": 5}], False)
    assert (first.quantity, second.quantity) == (0, 8)
    assert [(i.warehouse_id, i.quantity) for i in order.items] == [(1, 3), (2, 2)]
    assert order.total == Decimal("225.00")
    service.orders.add.assert_called_once_with(order)
    service.session.commit.assert_called_once()


def test_out_of_stock_rolls_back(service, user):
    service.warehouses.stock_for_product.return_value = [Stock(product_id=1, warehouse_id=1, quantity=2)]
    with pytest.raises(BusinessRuleError, match="Not enough"):
        service.create(user, [{"product_id": 1, "quantity": 5}], False)
    service.session.rollback.assert_called_once()
    service.session.commit.assert_not_called()


def test_prescription_required(service, user):
    service.products.get.return_value = Product(id=3, name="Амоксициллин", price=Decimal(210),
                                                prescription_required=True)
    with pytest.raises(BusinessRuleError) as error:
        service.create(user, [{"product_id": 3, "quantity": 1}], False)
    assert error.value.code == "PRESCRIPTION_REQUIRED"
    service.warehouses.stock_for_product.assert_not_called()


def test_loyalty_discount(service, user):
    service.orders.completed_total.return_value = Decimal("5000")
    service.warehouses.stock_for_product.return_value = [Stock(product_id=1, warehouse_id=1, quantity=100)]
    order = service.create(user, [{"product_id": 1, "quantity": 20}], False)
    assert (order.subtotal, order.discount, order.total) == (Decimal("900.00"), Decimal("45.00"), Decimal("855.00"))
    service.orders.completed_total.assert_called_once_with(10)


def test_unknown_product(service, user):
    service.products.get.return_value = None
    with pytest.raises(EntityNotFoundError):
        service.create(user, [{"product_id": 99, "quantity": 1}], False)


def test_cancel_returns_stock(service, user):
    stock = Stock(product_id=1, warehouse_id=2, quantity=0)
    order = Order(id=5, customer_id=10, status="created", items=[OrderItem(product_id=1, warehouse_id=2, quantity=4)])
    service.orders.get.return_value = order
    service.warehouses.stock.return_value = stock
    service.change_status(user, 5, "cancelled")
    assert order.status == "cancelled" and stock.quantity == 4
    service.warehouses.stock.assert_called_once_with(1, 2)


def test_foreign_order_forbidden(service, user):
    service.orders.get.return_value = Order(id=6, customer_id=99, status="created")
    with pytest.raises(ForbiddenError):
        service.get(user, 6)


@pytest.mark.parametrize("current, target", [("created", "completed"), ("completed", "cancelled"),
                                             ("cancelled", "paid")])
def test_invalid_transitions(service, current, target):
    admin = User(id=2, email="a@a.ru", role="ADMIN")
    service.orders.get.return_value = Order(id=7, customer_id=10, status=current, items=[])
    with pytest.raises(BusinessRuleError):
        service.change_status(admin, 7, target)
