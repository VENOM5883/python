import pytest

from app.database import Base, make_engine, make_session_factory
from app.seed import seed
from app.services.services import DuplicateError, NotFoundError, PharmacyError, PharmacyService


@pytest.fixture
def service():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = PharmacyService(make_session_factory(engine))
    seed(service)
    return service


def test_crud(service):
    medicine = service.add_medicine("Но-шпа", "Sanofi", "спазмолитики", "таблетки", 150, 30)
    assert service.get_medicine(medicine.id).name == "Но-шпа"
    service.update_medicine(medicine.id, price="170")
    assert str(service.get_medicine(medicine.id).price) == "170.00"
    service.delete_medicine(medicine.id)
    with pytest.raises(NotFoundError):
        service.get_medicine(medicine.id)


def test_duplicate(service):
    with pytest.raises(DuplicateError):
        service.add_medicine("Парацетамол", "X", "Y", "таблетки", 10, 1)
    with pytest.raises(DuplicateError):
        service.add_customer("Кто-то", "+79001112233")


def test_search_filter_sort(service):
    assert [m.name for m in service.search("Озон")] == ["Лоратадин", "Омепразол"]
    names = [m.name for m in service.filter("антибиотики", max_price=250, sort="-price")]
    assert names == ["Амоксициллин"]
    in_stock = service.filter("противоаллергические", in_stock=True)
    assert [m.name for m in in_stock] == ["Лоратадин"]
    prices = [m.price for m in service.list_medicines("-price")]
    assert prices == sorted(prices, reverse=True)


def test_purchase_transaction_and_discount(service):
    purchase = service.make_purchase(1, {2: 2, 9: 5})  # карта: скидка 5 %
    assert float(purchase.total) == round((89 * 2 + 38 * 5) * 0.95, 2)
    assert service.get_medicine(2).quantity == 78
    history = service.customer_purchases(1)
    assert len(history) == 2


def test_purchase_rollback(service):
    before = service.get_medicine(1).quantity
    with pytest.raises(PharmacyError):
        service.make_purchase(3, {1: 1, 7: 1})  # Цетиризин закончился
    assert service.get_medicine(1).quantity == before
    with pytest.raises(PharmacyError):
        service.make_purchase(3, {5: 1})  # нужен рецепт


def test_foreign_key_protection(service):
    with pytest.raises(PharmacyError):
        service.delete_medicine(1)  # есть в покупках


def test_statistics(service):
    stats = service.statistics()
    assert stats["count"] == 10 and stats["max_price"] == 320
