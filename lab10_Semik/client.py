"""HTTP-клиент для REST API записей на приём (requests)."""
import json

import requests

BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"Accept": "application/json"}

MENU = """
=========================
REST CLIENT — ЗАПИСИ НА ПРИЁМ
=========================
1. Получить список
2. Получить объект
3. Создать
4. Изменить (PUT)
5. Частично изменить (PATCH)
6. Удалить
7. Фильтрация
8. Сортировка
9. Свободные записи
0. Выход"""


def show(response: requests.Response) -> None:
    print(f"HTTP {response.status_code}")
    if response.content:
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))


def ask_fields(partial: bool = False) -> dict:
    names = {"doctor": "Врач", "specialty": "Специальность", "date": "Дата (ГГГГ-ММ-ДД)",
             "time": "Время (ЧЧ:ММ)", "cabinet": "Кабинет", "patient": "Пациент",
             "status": "Статус (free/booked/completed/cancelled)"}
    data = {}
    for key, title in names.items():
        value = input(f"{title}{' (Enter — пропустить)' if partial or key in ('patient', 'status') else ''}: ").strip()
        if value:
            data[key] = int(value) if key == "cabinet" and value.isdigit() else value
    return data


def main() -> None:
    session = requests.Session()
    session.headers.update(HEADERS)
    while True:
        print(MENU)
        choice = input("Выберите действие: ").strip()
        try:
            if choice == "1":
                show(session.get(f"{BASE_URL}/appointments", timeout=5))
            elif choice == "2":
                show(session.get(f"{BASE_URL}/appointments/{input('ID: ').strip()}", timeout=5))
            elif choice == "3":
                show(session.post(f"{BASE_URL}/appointments", json=ask_fields(), timeout=5))
            elif choice == "4":
                appointment_id = input("ID: ").strip()
                show(session.put(f"{BASE_URL}/appointments/{appointment_id}", json=ask_fields(),
                                 timeout=5))
            elif choice == "5":
                appointment_id = input("ID: ").strip()
                show(session.patch(f"{BASE_URL}/appointments/{appointment_id}",
                                   json=ask_fields(partial=True), timeout=5))
            elif choice == "6":
                show(session.delete(f"{BASE_URL}/appointments/{input('ID: ').strip()}", timeout=5))
            elif choice == "7":
                params = {k: input(f"{k} (Enter — любой): ").strip()
                          for k in ("doctor", "specialty", "status", "date")}
                show(session.get(f"{BASE_URL}/appointments",
                                 params={k: v for k, v in params.items() if v}, timeout=5))
            elif choice == "8":
                params = {"sort": input("Поле (datetime/doctor/cabinet/id): ").strip(),
                          "order": input("Порядок (asc/desc): ").strip() or "asc"}
                show(session.get(f"{BASE_URL}/appointments", params=params, timeout=5))
            elif choice == "9":
                specialty = input("Специальность (Enter — любая): ").strip()
                show(session.get(f"{BASE_URL}/appointments/free",
                                 params={"specialty": specialty} if specialty else {}, timeout=5))
            elif choice == "0":
                break
            else:
                print("Неизвестный пункт меню")
        except requests.RequestException as error:
            print("Ошибка соединения с сервером:", error)


if __name__ == "__main__":
    main()
