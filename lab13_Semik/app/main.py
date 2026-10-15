"""Лабораторная работа №13. MongoDB и Redis. Вариант 15 — Медицинская клиника (приёмы).
Запуск из папки lab13_Semik:  python -m app.main
"""
import json

from app.cache import RedisCache
from app.mongodb import get_database
from app.redis_client import get_redis
from app.repository import MongoRepository
from app.seed import generate
from app.service import ClinicService, NotFoundError

MENU = """
===== MENU =====
1. Add
2. Find (по id, через кэш)
3. List
4. Search (запросы MongoDB)
5. Update
6. Delete
7. Statistics (aggregation)
8. Cache status
9. Clear cache
10. Benchmark
0. Exit"""


def show(documents: list[dict]) -> None:
    for d in documents:
        print(f"  {d['_id']}  {d['date']} {d['time']}  {d['doctor']['full_name']:<27} "
              f"{d['patient']['full_name']:<27} {d['status']}")
    print(f"  Найдено: {len(documents)}")


def search_menu(service: ClinicService) -> None:
    repo = service.repository
    print("1) по статусу  2) специальность+дата  3) период  4) пациент (вложенное поле)\n"
          "5) назначение (массив)  6) ближайшие 5 (limit)  7) расписание врача (Redis List)")
    choice = input("Запрос: ").strip()
    if choice == "1":
        show(repo.by_status(input("Статус: ").strip()))
    elif choice == "2":
        show(repo.by_specialty_and_date(input("Специальность: ").strip(), input("Дата: ").strip()))
    elif choice == "3":
        show(repo.in_period(input("С (ГГГГ-ММ-ДД): ").strip(), input("По: ").strip()))
    elif choice == "4":
        show(service.search_patient(input("Часть ФИО: ").strip()))
    elif choice == "5":
        show(repo.by_prescription(input("Назначение: ").strip()))
    elif choice == "6":
        show(repo.upcoming(input("Начиная с даты: ").strip()))
    elif choice == "7":
        slots, source = service.doctor_schedule(int(input("ID врача: ")), input("Дата: ").strip())
        print(f"  Источник: {source}")
        for slot in slots:
            print("  ", slot)


def run(service: ClinicService) -> None:
    while True:
        print(MENU)
        choice = input("Выбор: ").strip()
        try:
            if choice == "1":
                doctor_id = int(input("ID врача (1-4): "))
                doctor = service.doctor_info(doctor_id)
                doctor = {k: (int(v) if k in ("id", "cabinet") else v)
                          for k, v in doctor.items() if k != "source"}
                created = service.add({
                    "patient": {"full_name": input("ФИО пациента: "),
                                "birth_year": int(input("Год рождения: ")),
                                "phone": input("Телефон: ")},
                    "doctor": doctor, "specialty": doctor["specialty"],
                    "date": input("Дата (ГГГГ-ММ-ДД): ").strip(), "time": input("Время (ЧЧ:ММ): ").strip()})
                print("Создан:", created["_id"])
            elif choice == "2":
                document = service.get(input("ID приёма: ").strip())
                print(f"Источник: {service.last_source}")
                print(json.dumps(document, ensure_ascii=False, indent=2))
            elif choice == "3":
                show(service.repository.list(sort=[("date", 1), ("time", 1)]))
            elif choice == "4":
                search_menu(service)
            elif choice == "5":
                appointment_id = input("ID приёма: ").strip()
                fields = {}
                status = input("Новый статус (Enter — не менять): ").strip()
                if status:
                    fields["status"] = status
                diagnosis = input("Диагноз (Enter — не менять): ").strip()
                if diagnosis:
                    fields["diagnosis"] = diagnosis
                prescription = input("Добавить назначение (Enter — нет): ").strip()
                if prescription:
                    service.repository.add_prescription(appointment_id, prescription)
                print("Обновлён:", service.update(appointment_id, fields or {"status": service.get(appointment_id)["status"]})["status"])
            elif choice == "6":
                service.delete(input("ID приёма: ").strip())
                print("Удалено")
            elif choice == "7":
                print(json.dumps(service.statistics(), ensure_ascii=False, indent=2))
            elif choice == "8":
                for key in service.cache.keys():
                    print(f"  {key} (TTL {service.cache.ttl(key)})")
                print("  Ближайшие приёмы (Sorted Set):", service.cache.nearest())
                print("  Последние запросы (List):", service.cache.recent_queries())
            elif choice == "9":
                service.cache.clear()
                print("Кэш очищен")
            elif choice == "10":
                appointment_id = service.repository.list(limit=1)[0]["_id"]
                print(f"{'Запросов':>10}{'MongoDB, с':>14}{'Redis, с':>12}{'MongoDB/запрос, мкс':>22}{'Redis/запрос, мкс':>20}")
                for count, mongo, redis in service.benchmark(appointment_id):
                    print(f"{count:>10}{mongo:>14.4f}{redis:>12.4f}{mongo / count * 1e6:>22.1f}{redis / count * 1e6:>20.1f}")
            elif choice == "0":
                return
            else:
                print("Неизвестный пункт")
        except (NotFoundError, ValueError, KeyError, TypeError) as error:
            print("Ошибка:", error)


def build_service() -> ClinicService:
    database, mongo_kind = get_database()
    redis, redis_kind = get_redis()
    print(f"MongoDB: {mongo_kind}; Redis: {redis_kind}")
    repository = MongoRepository(database)
    if repository.count() == 0:
        repository.insert_many(generate())
    print("Индексы:", repository.create_indexes())
    service = ClinicService(repository, RedisCache(redis))
    for document in repository.upcoming("2026-01-01", limit=100):
        service.cache.add_upcoming(document)
    return service


if __name__ == "__main__":
    run(build_service())
