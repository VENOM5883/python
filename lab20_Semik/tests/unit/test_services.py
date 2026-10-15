from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.models import Medicine, Sale
from src.services import ConflictError, NotFoundError, PharmacyService


@pytest.fixture
def session():
    session = MagicMock()
    session.get.return_value = Medicine(id=1, name="Парацетамол", category="обезболивающие",
                                        price=Decimal("45.00"), quantity=10)
    return session


def test_sell_decreases_stock_and_commits(session):
    sale = PharmacyService(session).sell(1, 3)
    assert isinstance(sale, Sale) and sale.total == Decimal("135.00")
    assert session.get.return_value.quantity == 7
    session.commit.assert_called_once()


@pytest.mark.parametrize("quantity, ok", [(10, True), (11, False)])
def test_sell_boundary(session, quantity, ok):
    if ok:
        PharmacyService(session).sell(1, quantity)
    else:
        with pytest.raises(ConflictError):
            PharmacyService(session).sell(1, quantity)
        session.commit.assert_not_called()


def test_get_missing(session):
    session.get.return_value = None
    with pytest.raises(NotFoundError):
        PharmacyService(session).get(42)
