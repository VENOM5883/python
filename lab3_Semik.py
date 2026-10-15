"""Лабораторная работа №3. Объектно-ориентированное программирование в Python.
Вариант 15. Серверный парк: Server -> WebServer, DatabaseServer; DataCenter.
"""
from abc import ABC, abstractmethod


class Hardware:
    """Аппаратная конфигурация сервера (используется через композицию)."""

    def __init__(self, cpu_cores, ram_gb):
        if cpu_cores <= 0 or ram_gb <= 0:
            raise ValueError("Количество ядер и объём RAM должны быть положительными")
        self.cpu_cores = cpu_cores
        self.ram_gb = ram_gb

    def __str__(self):
        return f"{self.cpu_cores} ядер / {self.ram_gb} ГБ RAM"


class Server(ABC):
    """Базовый класс сервера."""

    data_center_name = "DC-Moscow-1"

    def __init__(self, name, ip, hardware):
        self.name = name
        self.ip = ip
        self.hardware = hardware  # композиция: Server HAS-A Hardware
        self.cpu_load = 0.0
        self._is_running = False

    @property
    def cpu_load(self):
        return self._cpu_load

    @cpu_load.setter
    def cpu_load(self, value):
        if not 0 <= value <= 100:
            raise ValueError("Загрузка CPU должна быть в диапазоне от 0 до 100 %")
        self._cpu_load = float(value)

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        self._is_running = True

    def stop(self):
        self._is_running = False
        self.cpu_load = 0.0
        self.reset_activity()

    @abstractmethod
    def reset_activity(self):
        """Сбросить нагрузку, специфичную для типа сервера."""

    @abstractmethod
    def capacity(self):
        """Максимальная нагрузка, которую выдерживает сервер."""

    @abstractmethod
    def current_activity(self):
        """Текущая нагрузка (запросы или подключения)."""

    def evaluate_load(self):
        """Общий полиморфный метод оценки загрузки, %."""
        if not self.is_running:
            return 0.0
        activity_percent = self.current_activity() / self.capacity() * 100
        return round(min(100.0, max(self.cpu_load, activity_percent)), 1)

    def load_level(self):
        load = self.evaluate_load()
        if not self.is_running:
            return "остановлен"
        if load >= 90:
            return "критическая"
        if load >= 70:
            return "высокая"
        if load >= 30:
            return "нормальная"
        return "низкая"

    def get_info(self):
        state = "работает" if self.is_running else "остановлен"
        return (f"{type(self).__name__} {self.name} ({self.ip}), {self.hardware}, {state}, "
                f"CPU {self.cpu_load}%")

    def __str__(self):
        return self.get_info()

    def __lt__(self, other):
        return self.evaluate_load() < other.evaluate_load()


class WebServer(Server):
    REQUESTS_PER_CORE = 500

    def __init__(self, name, ip, hardware, framework):
        super().__init__(name, ip, hardware)
        self.framework = framework
        self._requests_per_second = 0

    @property
    def requests_per_second(self):
        return self._requests_per_second

    def handle_requests(self, count):
        if count < 0:
            raise ValueError("Количество запросов не может быть отрицательным")
        if not self.is_running:
            raise RuntimeError(f"Сервер {self.name} остановлен")
        self._requests_per_second = count

    def reset_activity(self):
        self._requests_per_second = 0

    def capacity(self):
        return self.hardware.cpu_cores * self.REQUESTS_PER_CORE

    def current_activity(self):
        return self._requests_per_second

    def get_info(self):
        return (super().get_info() +
                f", {self.framework}, {self._requests_per_second}/{self.capacity()} запросов/с")


class DatabaseServer(Server):
    CONNECTIONS_PER_GB = 10

    def __init__(self, name, ip, hardware, dbms):
        super().__init__(name, ip, hardware)
        self.dbms = dbms
        self._connections = 0

    @property
    def connections(self):
        return self._connections

    def open_connections(self, count):
        if not self.is_running:
            raise RuntimeError(f"Сервер {self.name} остановлен")
        if count < 0:
            raise ValueError("Количество подключений не может быть отрицательным")
        self._connections = min(self._connections + count, self.capacity())

    def close_connections(self, count):
        self._connections = max(0, self._connections - count)

    def reset_activity(self):
        self._connections = 0

    def capacity(self):
        return self.hardware.ram_gb * self.CONNECTIONS_PER_GB

    def current_activity(self):
        return self._connections

    def get_info(self):
        return (super().get_info() +
                f", {self.dbms}, {self._connections}/{self.capacity()} подключений")


class DataCenter:
    """Дата-центр содержит коллекцию серверов (композиция)."""

    def __init__(self, name):
        self.name = name
        self._servers = []

    def add_server(self, server):
        if self.find(server.name):
            raise ValueError(f"Сервер {server.name} уже существует")
        self._servers.append(server)

    def remove_server(self, name):
        server = self.find(name)
        if server is None:
            raise KeyError(f"Сервер {name} не найден")
        self._servers.remove(server)

    def find(self, name):
        for server in self._servers:
            if server.name == name:
                return server
        return None

    def find_by(self, server_type=None, min_load=0):
        return [s for s in self._servers
                if (server_type is None or isinstance(s, server_type))
                and s.evaluate_load() >= min_load]

    def average_load(self):
        running = [s for s in self._servers if s.is_running]
        if not running:
            return 0.0
        return round(sum(s.evaluate_load() for s in running) / len(running), 1)

    def most_loaded(self):
        return max(self._servers) if self._servers else None

    def sorted_by_load(self):
        return sorted(self._servers, reverse=True)

    def __len__(self):
        return len(self._servers)

    def __iter__(self):
        return iter(self._servers)


def print_report(dc):
    print(f"\n=== Дата-центр {dc.name}, серверов: {len(dc)} ===")
    for server in dc:  # полиморфный вызов evaluate_load()
        print(f"{server.name:<8} загрузка {server.evaluate_load():>5}% ({server.load_level()})")
    print(f"Средняя загрузка: {dc.average_load()}%")
    leader = dc.most_loaded()
    if leader:
        print(f"Наиболее загруженный: {leader.name}")


def create_demo():
    dc = DataCenter("DC-Moscow-1")
    dc.add_server(WebServer("web-1", "10.0.0.11", Hardware(4, 8), "nginx"))
    dc.add_server(WebServer("web-2", "10.0.0.12", Hardware(8, 16), "Apache"))
    dc.add_server(DatabaseServer("db-1", "10.0.0.21", Hardware(16, 64), "PostgreSQL"))
    dc.add_server(DatabaseServer("db-2", "10.0.0.22", Hardware(8, 32), "MySQL"))
    for server in dc:
        server.start()
    dc.find("web-1").handle_requests(1800)
    dc.find("web-1").cpu_load = 70
    dc.find("web-2").handle_requests(1200)
    dc.find("web-2").cpu_load = 25
    dc.find("db-1").open_connections(250)
    dc.find("db-1").cpu_load = 40
    dc.find("db-2").open_connections(310)
    dc.find("db-2").cpu_load = 88
    return dc


def demo():
    dc = create_demo()
    print("Тест 1. Созданные объекты:")
    for server in dc:
        print(" ", server)

    print_report(dc)  # тесты 2, 3, 6: общий метод, переопределения, полиморфная коллекция

    print("\nТест 4. Изменение состояния: на web-2 пришло 3900 запросов/с")
    dc.find("web-2").handle_requests(3900)
    print(" ", dc.find("web-2").get_info(), "->", dc.find("web-2").evaluate_load(), "%")
    dc.find("db-2").stop()
    print("  db-2 остановлен:", dc.find("db-2").load_level())

    print("\nТест 5. Некорректное значение свойства:")
    try:
        dc.find("web-1").cpu_load = 150
    except ValueError as error:
        print("  Ошибка:", error)
    try:
        Server("x", "1.1.1.1", Hardware(1, 1))
    except TypeError as error:
        print("  Нельзя создать абстрактный Server:", error)

    print("\nТест 7. Композиция:")
    print(f"  {dc.name} содержит серверов: {len(dc)}; web-1 содержит Hardware: {dc.find('web-1').hardware}")
    print("  Только БД-серверы:", [s.name for s in dc.find_by(DatabaseServer)])
    print("  Сортировка по загрузке:", [s.name for s in dc.sorted_by_load()])
    print_report(dc)


def menu():
    dc = create_demo()
    while True:
        print("\n===== МЕНЮ =====\n1. Создать сервер\n2. Показать серверы\n3. Нагрузить сервер\n"
              "4. Изменить загрузку CPU\n5. Удалить сервер\n6. Показать статистику\n"
              "7. Запустить демонстрацию\n0. Выход")
        choice = input("Выберите действие: ").strip()
        try:
            if choice == "1":
                kind = input("Тип (web/db): ").strip()
                name, ip = input("Имя: ").strip(), input("IP: ").strip()
                hardware = Hardware(int(input("Ядер CPU: ")), int(input("RAM, ГБ: ")))
                if kind == "web":
                    server = WebServer(name, ip, hardware, input("Веб-сервер (nginx...): "))
                else:
                    server = DatabaseServer(name, ip, hardware, input("СУБД: "))
                server.start()
                dc.add_server(server)
            elif choice == "2":
                for server in dc:
                    print(server)
            elif choice == "3":
                server = dc.find(input("Имя сервера: "))
                if isinstance(server, WebServer):
                    server.handle_requests(int(input("Запросов в секунду: ")))
                elif isinstance(server, DatabaseServer):
                    server.open_connections(int(input("Новых подключений: ")))
                else:
                    print("Сервер не найден")
            elif choice == "4":
                server = dc.find(input("Имя сервера: "))
                if server:
                    server.cpu_load = float(input("Загрузка CPU, %: "))
            elif choice == "5":
                dc.remove_server(input("Имя сервера: "))
            elif choice == "6":
                print_report(dc)
            elif choice == "7":
                demo()
            elif choice == "0":
                break
            else:
                print("Неизвестный пункт меню")
        except (ValueError, KeyError, RuntimeError) as error:
            print("Ошибка:", error)


if __name__ == "__main__":
    menu()
