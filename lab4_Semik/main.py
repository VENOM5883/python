"""Лабораторная работа №4. Модули, исключения, файлы и сериализация.
Вариант 15. Компьютерный магазин — каталог компьютерных конфигураций.
"""
from exceptions import ComputerStoreError
from services import SORT_KEYS, ComputerCatalog
import storage

MENU = """
===== КОМПЬЮТЕРНЫЙ МАГАЗИН =====
1. Добавить конфигурацию
2. Показать каталог
3. Изменить конфигурацию
4. Удалить конфигурацию
5. Поиск (по названию или процессору)
6. Фильтрация (RAM от / цена до)
7. Сортировка
8. Сохранить JSON
9. Экспортировать CSV
10. Загрузить JSON
0. Выход"""


def read_number(prompt, cast=float, allow_empty=False):
    while True:
        text = input(prompt).strip().replace(",", ".")
        if allow_empty and text == "":
            return None
        try:
            return cast(text)
        except ValueError:
            print("Ошибка: необходимо ввести число")


def show(computers):
    if not computers:
        print("Ничего не найдено.")
    for computer in computers:
        print(computer)


def handle(choice, catalog):
    if choice == "1":
        catalog.add(input("Название: "), input("Процессор: "), read_number("RAM, ГБ: ", int),
                    read_number("Накопитель, ГБ: ", int), read_number("Цена, руб.: "))
        print("Конфигурация добавлена.")
    elif choice == "2":
        show(catalog.computers)
        print(f"Всего: {len(catalog.computers)}, средняя цена: {catalog.average_price():.2f} руб.")
    elif choice == "3":
        name = input("Название изменяемой конфигурации: ")
        catalog.get(name)
        print("Оставьте поле пустым, чтобы не изменять его.")
        computer = catalog.update(
            name,
            cpu=input("Новый процессор: "),
            ram=read_number("Новый объём RAM: ", int, True),
            storage=read_number("Новый объём накопителя: ", int, True),
            price=read_number("Новая цена: ", float, True),
        )
        print("Изменено:", computer)
    elif choice == "4":
        catalog.delete(input("Название: "))
        print("Удалено.")
    elif choice == "5":
        show(catalog.search(input("Строка поиска: ")))
    elif choice == "6":
        min_ram = read_number("Минимальный объём RAM: ", int)
        max_price = read_number("Максимальная цена (Enter — без ограничения): ", float, True)
        show(catalog.filter(min_ram, max_price))
    elif choice == "7":
        key = input(f"Поле ({', '.join(SORT_KEYS)}): ").strip() or "price"
        if key not in SORT_KEYS:
            print("Неизвестное поле сортировки")
            return
        show(catalog.sort(key, input("По убыванию? (д/н): ").strip().lower() == "д"))
    elif choice == "8":
        storage.save_json(catalog.computers)
        print(f"Сохранено в {storage.JSON_PATH}")
    elif choice == "9":
        storage.export_csv(catalog.computers)
        print(f"Экспортировано в {storage.CSV_PATH}")
    elif choice == "10":
        catalog.__init__(storage.load_json())
        print(f"Загружено конфигураций: {len(catalog.computers)}")
    else:
        print("Неизвестный пункт меню")


def main():
    try:
        catalog = ComputerCatalog(storage.load_json())
        print(f"Загружено конфигураций: {len(catalog.computers)}")
    except ComputerStoreError as error:
        print("Ошибка загрузки:", error)
        catalog = ComputerCatalog()
    while True:
        print(MENU)
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            storage.save_json(catalog.computers)
            print("Данные сохранены. Выход.")
            break
        try:
            handle(choice, catalog)
        except ComputerStoreError as error:
            print("Ошибка:", error)
        except OSError as error:
            print("Ошибка работы с файлом:", error)


if __name__ == "__main__":
    main()
