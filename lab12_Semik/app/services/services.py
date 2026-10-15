"""Бизнес-логика аптеки. Каждая операция — отдельная транзакция Session."""
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError

from app.models import Purchase, PurchaseItem
from app.repositories.repositories import (MEDICINE_SORTS, CustomerRepository, MedicineRepository,
                                           PurchaseRepository)

CARD_DISCOUNT = Decimal("0.05")


class PharmacyError(Exception):
    pass


class NotFoundError(PharmacyError):
    pass


class DuplicateError(PharmacyError):
    pass


class PharmacyService:
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory

    @staticmethod
    def _money(value) -> Decimal:
        try:
            amount = Decimal(str(value)).quantize(Decimal("0.01"))
        except InvalidOperation:
            raise PharmacyError(f"Некорректная сумма: {value}") from None
        if amount <= 0:
            raise PharmacyError("Цена должна быть положительной")
        return amount

    # ---------- лекарства (CRUD основной сущности) ----------
    def add_medicine(self, name: str, manufacturer: str, category: str, form: str, price,
                     quantity: int, prescription_required: bool = False):
        if not name.strip():
            raise PharmacyError("Название не может быть пустым")
        if int(quantity) < 0:
            raise PharmacyError("Количество не может быть отрицательным")
        with self.session_factory() as session:
            try:
                medicine = MedicineRepository(session).create(
                    name=name.strip(), manufacturer=manufacturer.strip(), category=category.strip(),
                    form=form.strip(), price=self._money(price), quantity=int(quantity),
                    prescription_required=prescription_required)
                session.commit()
                return medicine
            except IntegrityError:
                session.rollback()
                raise DuplicateError(f"Препарат «{name}» ({form}) уже существует") from None

    def get_medicine(self, medicine_id: int):
        with self.session_factory() as session:
            medicine = MedicineRepository(session).get_by_id(medicine_id)
            if medicine is None:
                raise NotFoundError(f"Препарат {medicine_id} не найден")
            return medicine

    def list_medicines(self, sort: str = "name"):
        if sort not in MEDICINE_SORTS:
            raise PharmacyError(f"Сортировка: {', '.join(MEDICINE_SORTS)}")
        with self.session_factory() as session:
            return MedicineRepository(session).get_all(sort)

    def update_medicine(self, medicine_id: int, **fields):
        fields = {k: v for k, v in fields.items() if v not in (None, "")}
        if "price" in fields:
            fields["price"] = self._money(fields["price"])
        if "quantity" in fields and int(fields["quantity"]) < 0:
            raise PharmacyError("Количество не может быть отрицательным")
        with self.session_factory() as session:
            repository = MedicineRepository(session)
            medicine = repository.get_by_id(medicine_id)
            if medicine is None:
                raise NotFoundError(f"Препарат {medicine_id} не найден")
            try:
                repository.update(medicine, **fields)
                session.commit()
            except IntegrityError:
                session.rollback()
                raise DuplicateError("Препарат с таким названием и формой уже существует") from None
            return medicine

    def delete_medicine(self, medicine_id: int) -> None:
        with self.session_factory() as session:
            repository = MedicineRepository(session)
            medicine = repository.get_by_id(medicine_id)
            if medicine is None:
                raise NotFoundError(f"Препарат {medicine_id} не найден")
            try:
                repository.delete(medicine)
                session.commit()
            except IntegrityError:
                session.rollback()
                raise PharmacyError("Нельзя удалить препарат: он есть в покупках "
                                    "(нарушение внешнего ключа)") from None

    def search(self, text: str):
        with self.session_factory() as session:
            return MedicineRepository(session).search(text)

    def filter(self, category=None, max_price=None, in_stock=False, sort="price"):
        with self.session_factory() as session:
            return MedicineRepository(session).filter(
                category, self._money(max_price) if max_price else None, in_stock, sort)

    def statistics(self) -> dict:
        with self.session_factory() as session:
            return MedicineRepository(session).statistics()

    # ---------- покупатели ----------
    def add_customer(self, full_name: str, phone: str, discount_card: bool = False):
        if not full_name.strip() or not phone.strip():
            raise PharmacyError("ФИО и телефон обязательны")
        with self.session_factory() as session:
            try:
                customer = CustomerRepository(session).create(
                    full_name=full_name.strip(), phone=phone.strip(), discount_card=discount_card)
                session.commit()
                return customer
            except IntegrityError:
                session.rollback()
                raise DuplicateError(f"Покупатель с телефоном {phone} уже есть") from None

    def list_customers(self):
        with self.session_factory() as session:
            return CustomerRepository(session).get_all()

    def customer_purchases(self, customer_id: int):
        with self.session_factory() as session:
            repository = CustomerRepository(session)
            if repository.get_by_id(customer_id) is None:
                raise NotFoundError(f"Покупатель {customer_id} не найден")
            purchases = repository.purchases_of(customer_id)
            return [(p, [(i.medicine.name, i.quantity, i.price) for i in p.items]) for p in purchases]

    # ---------- транзакционная операция ----------
    def make_purchase(self, customer_id: int, items: dict[int, int],
                      has_prescription: bool = False) -> Purchase:
        """Покупка: проверка остатков, списание, создание покупки и позиций, расчёт суммы.
        Всё выполняется в одной транзакции: при любой ошибке — rollback."""
        if not items:
            raise PharmacyError("Корзина пуста")
        with self.session_factory() as session:
            try:
                customer = CustomerRepository(session).get_by_id(customer_id)
                if customer is None:
                    raise NotFoundError(f"Покупатель {customer_id} не найден")
                medicines = MedicineRepository(session)
                purchase = Purchase(customer=customer)
                session.add(purchase)
                total = Decimal("0")
                for medicine_id, quantity in items.items():
                    medicine = medicines.get_by_id(medicine_id)
                    if medicine is None:
                        raise NotFoundError(f"Препарат {medicine_id} не найден")
                    if quantity <= 0:
                        raise PharmacyError("Количество должно быть положительным")
                    if medicine.prescription_required and not has_prescription:
                        raise PharmacyError(f"«{medicine.name}» отпускается только по рецепту")
                    if medicine.quantity < quantity:
                        raise PharmacyError(f"Недостаточно «{medicine.name}»: в наличии "
                                            f"{medicine.quantity}, запрошено {quantity}")
                    medicine.quantity -= quantity
                    purchase.items.append(PurchaseItem(medicine=medicine, quantity=quantity,
                                                       price=medicine.price))
                    total += medicine.price * quantity
                if customer.discount_card:
                    total -= (total * CARD_DISCOUNT).quantize(Decimal("0.01"))
                purchase.total = total
                PurchaseRepository(session).add(purchase)
                session.commit()
                return purchase
            except Exception:
                session.rollback()
                raise
