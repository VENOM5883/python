from datetime import datetime

from factories.appointment_factory import AppointmentFactory
from services.service import AppointmentService
from strategies.pricing import PreferentialPricing, StandardPricing, UrgentPricing

STRATEGIES = {"1": StandardPricing, "2": PreferentialPricing, "3": UrgentPricing}


class ConsoleUI:
    def __init__(self, service: AppointmentService, statistics) -> None:
        self.service = service
        self.statistics = statistics

    def run(self) -> None:
        while True:
            print(f"\n=== ЗАПИСЬ НА ПРИЁМ (тариф: {self.service.strategy.name}) ===\n"
                  "1. Записать на приём\n2. Список записей\n3. Сменить тариф (Strategy)\n"
                  "4. Подтвердить\n5. Завершить приём\n6. Отменить\n7. Статистика\n0. Выход")
            choice = input("Выбор: ").strip()
            try:
                if choice == "1":
                    kind = input(f"Тип ({', '.join(AppointmentFactory.available())}): ").strip()
                    start = datetime.strptime(input("Дата (ДД.ММ.ГГГГ ЧЧ:ММ): "), "%d.%m.%Y %H:%M")
                    a = self.service.book(kind, input("Пациент: "), input("Врач: "), start)
                    print("Создано:", a.describe())
                elif choice == "2":
                    for a in self.service.repository.get_all():
                        print(a.describe())
                elif choice == "3":
                    strategy = STRATEGIES.get(input("1-стандартная, 2-льготная, 3-срочная: ").strip())
                    if strategy:
                        self.service.set_strategy(strategy())
                elif choice in ("4", "5", "6"):
                    action = {"4": self.service.confirm, "5": self.service.complete,
                              "6": self.service.cancel}[choice]
                    print(action(int(input("ID записи: "))).describe())
                elif choice == "7":
                    print(dict(self.statistics.events), f"выручка: {self.statistics.revenue:.2f}")
                elif choice == "0":
                    return
            except (ValueError, KeyError) as error:
                print("Ошибка:", error)
