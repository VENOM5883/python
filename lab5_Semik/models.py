"""Классы предметной области: компьютеры."""


class Computer:
    kind = "Компьютер"

    def __init__(self, name, cpu, ram, storage, price):
        if ram <= 0 or storage <= 0:
            raise ValueError("RAM и накопитель должны быть положительными")
        if price <= 0:
            raise ValueError("Цена должна быть положительной")
        self.name = name
        self.cpu = cpu
        self.ram = ram
        self.storage = storage
        self.price = price

    def __repr__(self):
        return (f"{self.kind:<9} {self.name:<16} {self.cpu:<17} RAM {self.ram:>3} ГБ "
                f"SSD {self.storage:>5} ГБ {self.price:>10.2f} руб.")


class Desktop(Computer):
    kind = "Desktop"

    def __init__(self, name, cpu, ram, storage, price, upgradable=True):
        super().__init__(name, cpu, ram, storage, price)
        self.upgradable = upgradable


class Laptop(Computer):
    kind = "Laptop"

    def __init__(self, name, cpu, ram, storage, price, battery_wh=50):
        super().__init__(name, cpu, ram, storage, price)
        self.battery_wh = battery_wh


class Monoblock(Computer):
    kind = "Monoblock"

    def __init__(self, name, cpu, ram, storage, price, screen_inches=24):
        super().__init__(name, cpu, ram, storage, price)
        self.screen_inches = screen_inches


def create_computers():
    return [
        Desktop("Office Mini", "Intel i3-12100", 8, 256, 35000),
        Desktop("Gamer Pro", "AMD Ryzen 7 7700", 32, 1000, 145000),
        Desktop("Workstation", "Intel i9-13900", 64, 2000, 260000),
        Laptop("Student Book", "AMD Ryzen 5 5600U", 16, 512, 58000, 56),
        Laptop("Ultra Slim", "Intel i7-1360P", 16, 1000, 112000, 70),
        Laptop("Budget Note", "Intel N100", 8, 256, 29000, 40),
        Monoblock("All-in-One 24", "Intel i5-12400", 16, 512, 74000, 24),
    ]
