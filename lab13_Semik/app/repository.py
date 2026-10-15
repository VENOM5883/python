"""MongoRepository: CRUD и запросы к коллекции appointments."""
from __future__ import annotations

from bson import ObjectId
from bson.errors import InvalidId


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError(f"Некорректный идентификатор: {value}") from None


def serialize(document: dict | None) -> dict | None:
    if document is None:
        return None
    return {**document, "_id": str(document["_id"])}


class MongoRepository:
    def __init__(self, database) -> None:
        self.collection = database["appointments"]

    def create_indexes(self) -> list[str]:
        return [
            # 1) расписание врача: фильтр по doctor.id + сортировка по дате/времени
            self.collection.create_index([("doctor.id", 1), ("date", 1), ("time", 1)],
                                         name="doctor_date_time"),
            # 2) выборки по статусу и специальности
            self.collection.create_index([("status", 1), ("specialty", 1)], name="status_specialty"),
        ]

    # ----- CRUD -----
    def insert(self, document: dict) -> str:
        return str(self.collection.insert_one(document).inserted_id)

    def insert_many(self, documents: list[dict]) -> int:
        return len(self.collection.insert_many(documents).inserted_ids)

    def get(self, appointment_id: str) -> dict | None:
        return serialize(self.collection.find_one({"_id": to_object_id(appointment_id)}))

    def list(self, query: dict | None = None, sort=None, limit: int = 0) -> list[dict]:
        cursor = self.collection.find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return [serialize(d) for d in cursor]

    def update(self, appointment_id: str, fields: dict) -> bool:
        result = self.collection.update_one({"_id": to_object_id(appointment_id)}, {"$set": fields})
        return result.matched_count == 1

    def add_prescription(self, appointment_id: str, prescription: str) -> bool:
        result = self.collection.update_one({"_id": to_object_id(appointment_id)},
                                            {"$push": {"prescriptions": prescription}})
        return result.matched_count == 1

    def delete(self, appointment_id: str) -> bool:
        return self.collection.delete_one({"_id": to_object_id(appointment_id)}).deleted_count == 1

    def count(self, query: dict | None = None) -> int:
        return self.collection.count_documents(query or {})

    # ----- запросы -----
    def by_status(self, status: str) -> list[dict]:                       # фильтр 1
        return self.list({"status": status}, [("date", 1), ("time", 1)])  # + сортировка 1

    def by_specialty_and_date(self, specialty: str, date: str) -> list[dict]:  # фильтр 2
        return self.list({"specialty": specialty, "date": date}, [("time", 1)])

    def in_period(self, date_from: str, date_to: str) -> list[dict]:         # фильтр 3
        return self.list({"date": {"$gte": date_from, "$lte": date_to},
                          "status": {"$ne": "cancelled"}}, [("date", -1), ("time", -1)])  # сортировка 2

    def by_patient_name(self, text: str) -> list[dict]:                     # вложенное поле
        return self.list({"patient.full_name": {"$regex": text, "$options": "i"}})

    def by_prescription(self, medicine: str) -> list[dict]:                  # элемент массива
        return self.list({"prescriptions": medicine})

    def doctor_schedule(self, doctor_id: int, date: str) -> list[dict]:
        return self.list({"doctor.id": doctor_id, "date": date, "status": {"$ne": "cancelled"}},
                         [("time", 1)])

    def upcoming(self, from_date: str, limit: int = 5) -> list[dict]:        # ограничение
        return self.list({"date": {"$gte": from_date}, "status": {"$in": ["planned", "confirmed"]}},
                         [("date", 1), ("time", 1)], limit)

    def count_by_status(self) -> list[dict]:                                 # агрегация 1
        return list(self.collection.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}]))

    def doctors_workload(self) -> list[dict]:                                # агрегация 2
        return list(self.collection.aggregate([
            {"$match": {"status": {"$ne": "cancelled"}}},
            {"$group": {"_id": "$doctor.full_name", "appointments": {"$sum": 1},
                        "specialty": {"$first": "$specialty"}}},
            {"$sort": {"appointments": -1}}]))

    def top_prescriptions(self, limit: int = 5) -> list[dict]:               # агрегация 3 ($unwind)
        return list(self.collection.aggregate([
            {"$unwind": "$prescriptions"},
            {"$group": {"_id": "$prescriptions", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}}, {"$limit": limit}]))
