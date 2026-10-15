"""Модель предметной области: компьютерная конфигурация."""
from exceptions import InvalidComputerDataError


class Computer:
    def __init__(self, name, cpu, ram, storage, price):
        self.name = name
        self.cpu = cpu
        self.ram = ram
        self.storage = storage
        self.price = price

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        value = str(value).strip()
        if not value:
            raise InvalidComputerDataError("Название не может быть пустым")
        self._name = value

    @property
    def cpu(self):
        return self._cpu

    @cpu.setter
    def cpu(self, value):
        value = str(value).strip()
        if not value:
            raise InvalidComputerDataError("Процессор не может быть пустым")
        self._cpu = value

    @property
    def ram(self):
        return self._ram

    @ram.setter
    def ram(self, value):
        value = int(value)
        if value <= 0:
            raise InvalidComputerDataError("Объём RAM должен быть положительным")
        self._ram = value

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, value):
        value = int(value)
        if value <= 0:
            raise InvalidComputerDataError("Объём накопителя должен быть положительным")
        self._storage = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        value = float(value)
        if value <= 0:
            raise InvalidComputerDataError("Цена должна быть положительной")
        self._price = value

    def to_dict(self):
        return {
            "name": self.name,
            "cpu": self.cpu,
            "ram": self.ram,
            "storage": self.storage,
            "price": self.price,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["cpu"], data["ram"], data["storage"], data["price"])

    def __str__(self):
        return (f"{self.name:<18} {self.cpu:<16} RAM {self.ram:>3} ГБ  "
                f"SSD {self.storage:>5} ГБ  {self.price:>10.2f} руб.")
