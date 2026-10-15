"""Пользовательские исключения предметной области."""


class ComputerStoreError(Exception):
    """Базовое исключение каталога."""


class ComputerNotFoundError(ComputerStoreError):
    def __init__(self, name):
        super().__init__(f"Компьютер «{name}» не найден")


class DuplicateComputerError(ComputerStoreError):
    def __init__(self, name):
        super().__init__(f"Компьютер «{name}» уже есть в каталоге")


class InvalidComputerDataError(ComputerStoreError):
    """Некорректные характеристики конфигурации."""


class StorageError(ComputerStoreError):
    """Ошибка чтения/записи файла данных."""
