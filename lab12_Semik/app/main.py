"""Лабораторная работа №12. SQLAlchemy ORM. Вариант 15 — Аптека.
Запуск из папки lab12_Semik:  python -m app.main
"""
from app.database import DATABASE_URL, Base, make_engine, make_session_factory
from app.seed import seed
from app.services.services import PharmacyError, PharmacyService

MENU = """
===== АПТЕКА =====
1. Список препаратов (сортировка)
2. Препарат по ID
3. Добавить препарат
4. Изменить препарат
5. Удалить препарат
6. Поиск по названию/производителю
7. Фильтрация (категория, цена до, в наличии)
8. Покупатели
9. Добавить покупателя
10. Покупки покупателя (связанные объекты)
11. Оформить покупку (транзакция)
12. Статистика (COUNT/SUM/AVG/MIN/MAX)
0. Выход"""


def ask_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Введите целое число")


def show(items) -> None:
    for item in items:
        print(" ", item)
    if not items:
        print("  Ничего не найдено")


def run(service: PharmacyService) -> None:
    while True:
        print(MENU)
        choice = input("Выбор: ").strip()
        try:
            if choice == "1":
                show(service.list_medicines(input("Сортировка (name/price/-price/quantity): ").strip() or "name"))
            elif choice == "2":
                print(service.get_medicine(ask_int("ID: ")))
            elif choice == "3":
                print("Добавлено:", service.add_medicine(
                    input("Название: "), input("Производитель: "), input("Категория: "),
                    input("Форма: "), input("Цена: "), ask_int("Количество: "),
                    input("Только по рецепту? (д/н): ").strip().lower() == "д"))
            elif choice == "4":
                medicine_id = ask_int("ID: ")
                print("Enter — оставить без изменений")
                print("Изменено:", service.update_medicine(
                    medicine_id, name=input("Название: ").strip(), price=input("Цена: ").strip(),
                    quantity=input("Количество: ").strip() or None))
            elif choice == "5":
                service.delete_medicine(ask_int("ID: "))
                print("Удалено")
            elif choice == "6":
                show(service.search(input("Строка поиска: ")))
            elif choice == "7":
                show(service.filter(input("Категория (Enter — любая): ").strip() or None,
                                    input("Цена до (Enter — без ограничения): ").strip() or None,
                                    input("Только в наличии? (д/н): ").strip().lower() == "д"))
            elif choice == "8":
                show(service.list_customers())
            elif choice == "9":
                print("Добавлен:", service.add_customer(input("ФИО: "), input("Телефон: "),
                                                        input("Скидочная карта? (д/н): ") == "д"))
            elif choice == "10":
                for purchase, items in service.customer_purchases(ask_int("ID покупателя: ")):
                    print(purchase)
                    for name, quantity, price in items:
                        print(f"    {name} × {quantity} по {price} руб.")
            elif choice == "11":
                customer_id = ask_int("ID покупателя: ")
                items = {}
                while True:
                    medicine_id = input("ID препарата (Enter — завершить): ").strip()
                    if not medicine_id:
                        break
                    items[int(medicine_id)] = ask_int("Количество: ")
                purchase = service.make_purchase(customer_id, items,
                                                 input("Есть рецепт? (д/н): ").strip() == "д")
                print(f"Покупка #{purchase.id} оформлена. Сумма: {purchase.total} руб.")
            elif choice == "12":
                for key, value in service.statistics().items():
                    print(f"  {key}: {value}")
            elif choice == "0":
                return
            else:
                print("Неизвестный пункт")
        except (PharmacyError, ValueError) as error:
            print("Ошибка:", error)


def main() -> None:
    engine = make_engine()
    Base.metadata.create_all(engine)
    print("Подключено к:", engine.url.render_as_string(hide_password=True))
    service = PharmacyService(make_session_factory(engine))
    seed(service)
    run(service)


if __name__ == "__main__":
    main()
