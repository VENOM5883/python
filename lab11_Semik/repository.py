"""Repository: только параметризованные SQL-запросы."""
import sqlite3

APPOINTMENT_SELECT = """
SELECT a.id, a.doctor_id, d.full_name AS doctor, d.specialty, d.cabinet,
       a.patient_id, p.full_name AS patient, a.date, a.time, a.status
FROM appointments a
JOIN doctors d ON d.id = a.doctor_id
LEFT JOIN patients p ON p.id = a.patient_id
"""
SORT_COLUMNS = {"datetime": "a.date, a.time", "doctor": "d.full_name", "cabinet": "d.cabinet",
                "id": "a.id"}


class AppointmentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.db = connection

    def get_all(self, filters: dict | None = None, sort: str = "id", order: str = "asc") -> list[dict]:
        conditions, params = [], []
        columns = {"doctor_id": "a.doctor_id", "specialty": "d.specialty", "status": "a.status",
                   "date": "a.date"}
        for key, value in (filters or {}).items():
            if value:
                conditions.append(f"{columns[key]} = ?")  # имя колонки — из белого списка
                params.append(value)
        sql = APPOINTMENT_SELECT
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        direction = "DESC" if order == "desc" else "ASC"
        sql += " ORDER BY " + ", ".join(f"{col} {direction}" for col in SORT_COLUMNS[sort].split(", "))
        return [dict(row) for row in self.db.execute(sql, params)]

    def get_by_id(self, appointment_id: int) -> dict | None:
        row = self.db.execute(APPOINTMENT_SELECT + " WHERE a.id = ?", (appointment_id,)).fetchone()
        return dict(row) if row else None

    def create(self, data: dict) -> int:
        cursor = self.db.execute(
            "INSERT INTO appointments (doctor_id, patient_id, date, time, status) VALUES (?, ?, ?, ?, ?)",
            (data["doctor_id"], data.get("patient_id"), data["date"], data["time"],
             data.get("status", "free")))
        self.db.commit()
        return cursor.lastrowid

    def update(self, appointment_id: int, data: dict) -> None:
        allowed = ("doctor_id", "patient_id", "date", "time", "status")
        assignments = ", ".join(f"{key} = ?" for key in data if key in allowed)
        values = [data[key] for key in data if key in allowed]
        self.db.execute(f"UPDATE appointments SET {assignments} WHERE id = ?", (*values, appointment_id))
        self.db.commit()

    def delete(self, appointment_id: int) -> bool:
        cursor = self.db.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def exists(self, table: str, entity_id: int) -> bool:
        assert table in ("doctors", "patients", "services")
        return self.db.execute(f"SELECT 1 FROM {table} WHERE id = ?", (entity_id,)).fetchone() is not None

    def doctor_schedule(self, doctor_id: int, date: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT a.id, a.time, a.status, p.full_name AS patient FROM appointments a "
            "LEFT JOIN patients p ON p.id = a.patient_id "
            "WHERE a.doctor_id = ? AND a.date = ? ORDER BY a.time", (doctor_id, date))
        return [dict(row) for row in rows]

    def doctor(self, doctor_id: int) -> dict | None:
        row = self.db.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
        return dict(row) if row else None

    def complete_with_services(self, appointment_id: int, services: list[dict]) -> float:
        """Транзакция: статус приёма + оказанные услуги. Ошибка на любом шаге -> ROLLBACK."""
        try:
            with self.db:  # BEGIN ... COMMIT / ROLLBACK
                cursor = self.db.execute(
                    "UPDATE appointments SET status = 'completed' "
                    "WHERE id = ? AND status = 'booked'", (appointment_id,))
                if cursor.rowcount == 0:
                    raise ValueError("Завершить можно только запись в статусе booked")
                for item in services:
                    self.db.execute(
                        "INSERT INTO appointment_services (appointment_id, service_id, quantity) "
                        "VALUES (?, ?, ?)", (appointment_id, item["service_id"], item.get("quantity", 1)))
        except sqlite3.IntegrityError as error:
            raise ValueError(f"Ошибка данных, транзакция отменена: {error}") from error
        return self.db.execute(
            "SELECT COALESCE(SUM(s.price * aps.quantity), 0) FROM appointment_services aps "
            "JOIN services s ON s.id = aps.service_id WHERE aps.appointment_id = ?",
            (appointment_id,)).fetchone()[0]
