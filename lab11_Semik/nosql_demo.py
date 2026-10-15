"""Демонстрация Redis (минимум 5 операций) и сравнение SQL / документной модели."""
import json

from cache import ScheduleCache, create_redis
from database import connect, init_db
from repository import AppointmentRepository
from service import AppointmentService


def main() -> None:
    redis = create_redis()
    print("Клиент Redis:", type(redis).__module__)
    redis.set("demo:key", "value")                      # SET
    print("GET:", redis.get("demo:key"))                # GET
    redis.expire("demo:key", 30)                        # EXPIRE
    print("TTL:", redis.ttl("demo:key"))
    print("INCR:", redis.incr("demo:counter"), redis.incr("demo:counter"))  # INCR
    redis.delete("demo:key")                            # DELETE
    print("После DELETE:", redis.get("demo:key"))

    connection = connect(":memory:")
    init_db(connection)
    service = AppointmentService(AppointmentRepository(connection), ScheduleCache(redis))
    for attempt in range(1, 3):
        result = service.schedule(1, "2026-10-20")
        print(f"Запрос расписания №{attempt}: источник = {result['source']}, TTL = {result['ttl']}")
    service.update(3, {"patient_id": 5}, partial=True)  # изменение -> инвалидирование
    print("После записи пациента источник =", service.schedule(1, "2026-10-20")["source"])

    print("\nТа же информация в виде документа (MongoDB-подобная модель):")
    document = {"doctor": result["doctor"], "date": result["date"], "slots": result["slots"]}
    print(json.dumps(document, ensure_ascii=False, indent=2))
    print("В SQL эти данные собираются JOIN-ом таблиц appointments, doctors, patients.")


if __name__ == "__main__":
    main()
