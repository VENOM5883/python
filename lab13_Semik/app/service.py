"""Бизнес-логика: MongoDB — основное хранилище, Redis — кэш и быстрые структуры."""
import time

from app.cache import RedisCache
from app.models import STATUSES, Appointment
from app.repository import MongoRepository


class NotFoundError(Exception):
    pass


class ClinicService:
    def __init__(self, repository: MongoRepository, cache: RedisCache) -> None:
        self.repository = repository
        self.cache = cache
        self.last_source = ""

    def add(self, data: dict) -> dict:
        appointment_id = self.repository.insert(Appointment(**data).to_document())
        created = self.repository.get(appointment_id)
        self._on_change(created)
        return created

    def get(self, appointment_id: str) -> dict:
        """Cache-Aside: Redis -> (промах) MongoDB -> Redis."""
        cached = self.cache.get_appointment(appointment_id)
        if cached is not None:
            self.last_source = "Redis (cache hit)"
            return cached
        document = self.repository.get(appointment_id)
        if document is None:
            raise NotFoundError(f"Приём {appointment_id} не найден")
        self.cache.set_appointment(document)
        self.last_source = "MongoDB (cache miss)"
        return document

    def update(self, appointment_id: str, fields: dict) -> dict:
        if "status" in fields and fields["status"] not in STATUSES:
            raise ValueError(f"status должен быть одним из {STATUSES}")
        before = self.repository.get(appointment_id)
        if before is None or not self.repository.update(appointment_id, fields):
            raise NotFoundError(f"Приём {appointment_id} не найден")
        self.cache.invalidate_appointment(appointment_id)          # инвалидирование
        after = self.repository.get(appointment_id)
        self._on_change(before)
        self._on_change(after)
        return after

    def delete(self, appointment_id: str) -> None:
        document = self.repository.get(appointment_id)
        if document is None or not self.repository.delete(appointment_id):
            raise NotFoundError(f"Приём {appointment_id} не найден")
        self.cache.invalidate_appointment(appointment_id)
        self.cache.remove_upcoming(appointment_id)
        self.cache.invalidate_schedule(document["doctor"]["id"], document["date"])

    def _on_change(self, document: dict) -> None:
        self.cache.invalidate_schedule(document["doctor"]["id"], document["date"])
        if document["status"] in ("planned", "confirmed"):
            self.cache.add_upcoming(document)
        else:
            self.cache.remove_upcoming(document["_id"])

    def doctor_schedule(self, doctor_id: int, date: str) -> tuple[list[str], str]:
        slots = self.cache.get_schedule(doctor_id, date)
        if slots is not None:
            return slots, "Redis"
        documents = self.repository.doctor_schedule(doctor_id, date)
        slots = [f"{d['time']} {d['patient']['full_name']} [{d['status']}]" for d in documents]
        self.cache.set_schedule(doctor_id, date, slots)
        if documents:
            self.cache.set_doctor(documents[0]["doctor"])
        return slots, "MongoDB"

    def doctor_info(self, doctor_id: int) -> dict:
        info = self.cache.get_doctor(doctor_id)
        if info:
            return {**info, "source": "Redis"}
        documents = self.repository.list({"doctor.id": doctor_id}, limit=1)
        if not documents:
            raise NotFoundError(f"Врач {doctor_id} не найден")
        self.cache.set_doctor(documents[0]["doctor"])
        return {**documents[0]["doctor"], "source": "MongoDB"}

    def search_patient(self, text: str) -> list[dict]:
        self.cache.log_query(text)
        return self.repository.by_patient_name(text)

    def statistics(self) -> dict:
        return {"total": self.repository.count(),
                "by_status": {r["_id"]: r["count"] for r in self.repository.count_by_status()},
                "doctors": [(r["_id"], r["appointments"]) for r in self.repository.doctors_workload()],
                "top_prescriptions": [(r["_id"], r["count"]) for r in self.repository.top_prescriptions()]}

    def benchmark(self, appointment_id: str, counts=(100, 1000, 10000)) -> list[tuple]:
        results = []
        for count in counts:
            start = time.perf_counter()
            for _ in range(count):
                self.repository.get(appointment_id)
            mongo = time.perf_counter() - start
            self.get(appointment_id)  # прогреть кэш
            start = time.perf_counter()
            for _ in range(count):
                self.cache.get_appointment(appointment_id)
            redis = time.perf_counter() - start
            results.append((count, mongo, redis))
        return results
