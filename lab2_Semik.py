"""Лабораторная работа №2. Коллекции, строки и функции в Python.
Вариант 15. Серверы.
"""
DEMO_SERVERS = [
    {"name": "web-01", "ip": "10.0.0.11", "purpose": "web", "ram": 16, "cpu": 45.5},
    {"name": "web-02", "ip": "10.0.0.12", "purpose": "web", "ram": 16, "cpu": 81.0},
    {"name": "db-01", "ip": "10.0.0.21", "purpose": "database", "ram": 64, "cpu": 92.3},
    {"name": "cache-01", "ip": "10.0.0.31", "purpose": "cache", "ram": 32, "cpu": 12.0},
    {"name": "backup-01", "ip": "10.0.0.41", "purpose": "backup", "ram": 8, "cpu": 0.0},
    {"name": "db-02", "ip": "10.0.0.22", "purpose": "database", "ram": 64, "cpu": 100.0},
]


def is_valid_ip(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True


def read_number(prompt, cast=float, minimum=None, maximum=None):
    while True:
        try:
            value = cast(input(prompt).replace(",", "."))
        except ValueError:
            print("Ошибка: введите число")
            continue
        if minimum is not None and value < minimum or maximum is not None and value > maximum:
            print(f"Ошибка: значение должно быть в диапазоне [{minimum}; {maximum}]")
            continue
        return value


def input_server(servers):
    name = input("Имя сервера: ").strip()
    if not name:
        print("Ошибка: имя не может быть пустым")
        return
    if name in {server["name"] for server in servers}:
        print("Ошибка: сервер с таким именем уже существует")
        return
    ip = input("IP-адрес: ").strip()
    if not is_valid_ip(ip):
        print("Ошибка: некорректный IP-адрес")
        return
    purpose = input("Назначение (web, database, cache...): ").strip().lower()
    ram = read_number("Объём RAM, ГБ: ", int, 1)
    cpu = read_number("Загрузка CPU, %: ", float, 0, 100)
    servers.append({"name": name, "ip": ip, "purpose": purpose, "ram": ram, "cpu": cpu})
    print("Сервер добавлен.")


def print_servers(servers, title="Серверы"):
    print(f"\n--- {title} ({len(servers)}) ---")
    if not servers:
        print("Нет подходящих серверов.")
        return
    print(f"{'Имя':<12}{'IP':<16}{'Назначение':<12}{'RAM':>6}{'CPU, %':>9}")
    for server in servers:
        print(f"{server['name']:<12}{server['ip']:<16}{server['purpose']:<12}"
              f"{server['ram']:>6}{server['cpu']:>9.1f}")


def find_by_purpose(servers, purpose):
    return [server for server in servers if server["purpose"] == purpose.lower()]


def filter_by_cpu(servers, minimum, maximum=100):
    return [server for server in servers if minimum <= server["cpu"] <= maximum]


def calculate_average_cpu(servers):
    total = 0
    for server in servers:
        total += server["cpu"]
    return total / len(servers) if servers else 0


def find_most_loaded(servers):
    most_loaded = servers[0]
    for server in servers:
        if server["cpu"] > most_loaded["cpu"]:
            most_loaded = server
    return most_loaded


def get_purposes(servers):
    return {server["purpose"] for server in servers}


def sort_by_cpu(servers, descending=True):
    return sorted(servers, key=lambda server: server["cpu"], reverse=descending)


def group_by_purpose(servers):
    groups = {}
    for server in servers:
        groups.setdefault(server["purpose"], []).append(server["name"])
    return groups


def print_statistics(servers):
    if not servers:
        print("Список серверов пуст.")
        return
    most_loaded = find_most_loaded(servers)
    overloaded = filter_by_cpu(servers, 80.01)
    print("\n--- Статистика ---")
    print(f"Количество серверов: {len(servers)}")
    print(f"Средняя загрузка CPU: {calculate_average_cpu(servers):.2f} %")
    print(f"Наиболее загруженный: {most_loaded['name']} ({most_loaded['cpu']} %)")
    print(f"Минимальная загрузка: {min(server['cpu'] for server in servers)} %")
    print(f"Суммарный объём RAM: {sum(server['ram'] for server in servers)} ГБ")
    print(f"Перегруженных (>80 %): {len(overloaded)}")
    for purpose, names in group_by_purpose(servers).items():
        print(f"  {purpose}: {', '.join(names)}")


def menu():
    servers = [dict(server) for server in DEMO_SERVERS]
    actions = (
        "\n===== МЕНЮ =====\n1. Добавить сервер\n2. Показать серверы\n3. Найти по назначению\n"
        "4. Фильтрация по загрузке CPU\n5. Сортировка по загрузке\n6. Статистика\n"
        "7. Уникальные назначения\n0. Выход"
    )
    while True:
        print(actions)
        choice = input("Выберите действие: ").strip()
        if choice == "1":
            input_server(servers)
        elif choice == "2":
            print_servers(servers)
        elif choice == "3":
            purpose = input("Назначение: ").strip()
            print_servers(find_by_purpose(servers, purpose), f"Назначение «{purpose}»")
        elif choice == "4":
            minimum = read_number("Минимальная загрузка, %: ", float, 0, 100)
            maximum = read_number("Максимальная загрузка, %: ", float, minimum, 100)
            print_servers(filter_by_cpu(servers, minimum, maximum), "Фильтр по CPU")
        elif choice == "5":
            print_servers(sort_by_cpu(servers), "По убыванию загрузки")
        elif choice == "6":
            print_statistics(servers)
        elif choice == "7":
            print("Назначения серверов:", ", ".join(sorted(get_purposes(servers))))
        elif choice == "0":
            print("Выход.")
            break
        else:
            print("Неизвестный пункт меню.")


if __name__ == "__main__":
    menu()
