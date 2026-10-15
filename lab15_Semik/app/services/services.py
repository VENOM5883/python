"""Бизнес-логика аптеки (не зависит от Flask)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError

from app.models.models import Category, Medicine, Purchase, PurchaseItem
from app.repositories.repositories import CategoryRepository, MedicineRepository, PurchaseRepository


class ServiceError(Exception):
    status = 400


class NotFound(ServiceError):
    status = 404


class Conflict(ServiceError):
    status = 409


class PharmacyService:
    def __init__(self, session) -> None:
        self.session = session
        self.medicines = MedicineRepository(session)
        self.categories = CategoryRepository(session)
        self.purchases = PurchaseRepository(session)

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise Conflict("Конфликт данных: объект с таким названием уже существует "
                           "или используется в других записях") from error

    def _clean(self, data: dict, partial: bool = False) -> dict:
        fields = {}
        required = ("name", "manufacturer", "form", "price", "quantity", "category_id")
        if not partial:
            missing = [f for f in required if str(data.get(f, "")).strip() == ""]
            if missing:
                raise ServiceError(f"Заполните поля: {', '.join(missing)}")
        for key in ("name", "manufacturer", "form"):
            if key in data and str(data[key]).strip():
                fields[key] = str(data[key]).strip()
        try:
            if str(data.get("price", "")).strip():
                fields["price"] = Decimal(str(data["price"]).replace(",", ".")).quantize(Decimal("0.01"))
                if fields["price"] <= 0:
                    raise ServiceError("Цена должна быть больше нуля")
            if str(data.get("quantity", "")).strip():
                fields["quantity"] = int(data["quantity"])
                if fields["quantity"] < 0:
                    raise ServiceError("Количество не может быть отрицательным")
            if str(data.get("category_id", "")).strip():
                fields["category_id"] = int(data["category_id"])
                if self.categories.get(fields["category_id"]) is None:
                    raise ServiceError("Категория не существует")
        except (InvalidOperation, ValueError):
            raise ServiceError("Цена, количество и категория должны быть числами") from None
        if "prescription_required" in data:
            value = data["prescription_required"]
            fields["prescription_required"] = value in (True, "on", "true", "1", 1)
        return fields

    def list_medicines(self, **filters) -> list[Medicine]:
        return self.medicines.list(**filters)

    def get_medicine(self, medicine_id: int) -> Medicine:
        medicine = self.medicines.get(medicine_id)
        if medicine is None:
            raise NotFound(f"Препарат {medicine_id} не найден")
        return medicine

    def create_medicine(self, data: dict) -> Medicine:
        medicine = Medicine(**self._clean(data))
        self.medicines.add(medicine)
        self._commit()
        return medicine

    def update_medicine(self, medicine_id: int, data: dict, partial: bool = True) -> Medicine:
        medicine = self.get_medicine(medicine_id)
        for key, value in self._clean(data, partial).items():
            setattr(medicine, key, value)
        self._commit()
        return medicine

    def delete_medicine(self, medicine_id: int) -> None:
        medicine = self.get_medicine(medicine_id)
        if medicine.items:
            raise Conflict("Препарат уже продавался — удалить нельзя, обнулите остаток")
        self.medicines.delete(medicine)
        self._commit()

    def list_categories(self) -> list[Category]:
        return self.categories.list()

    def get_category(self, category_id: int) -> Category:
        category = self.categories.get(category_id)
        if category is None:
            raise NotFound(f"Категория {category_id} не найдена")
        return category

    def create_purchase(self, customer_name: str, items: dict[int, int]) -> Purchase:
        """Оформление покупки в одной транзакции: проверка остатков, списание, расчёт суммы."""
        if not customer_name.strip():
            raise ServiceError("Укажите покупателя")
        items = {mid: qty for mid, qty in items.items() if qty > 0}
        if not items:
            raise ServiceError("Не выбрано ни одного препарата")
        try:
            purchase = Purchase(customer_name=customer_name.strip())
            self.session.add(purchase)
            total = Decimal("0")
            for medicine_id, quantity in items.items():
                medicine = self.get_medicine(medicine_id)
                if medicine.quantity < quantity:
                    raise Conflict(f"Недостаточно «{medicine.name}»: в наличии {medicine.quantity}")
                medicine.quantity -= quantity
                purchase.items.append(PurchaseItem(medicine=medicine, quantity=quantity, price=medicine.price))
                total += medicine.price * quantity
            purchase.total = total
            self.purchases.add(purchase)
            self._commit()
            return purchase
        except Exception:
            self.session.rollback()
            raise

    def list_purchases(self) -> list[Purchase]:
        return self.purchases.list()

    def stats(self) -> dict:
        medicines = self.medicines.list()
        return {"medicines": len(medicines), "categories": len(self.categories.list()),
                "purchases": len(self.purchases.list()),
                "out_of_stock": sum(1 for m in medicines if m.quantity == 0)}
