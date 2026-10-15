"""Repository: параметризованные SQL-запросы."""
import sqlite3


class ClinicRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.db = connection

    def _all(self, sql: str, params=()) -> list[dict]:
        return [dict(row) for row in self.db.execute(sql, params)]

    def _one(self, sql: str, params=()) -> dict | None:
        row = self.db.execute(sql, params).fetchone()
        return dict(row) if row else None

    def specialties(self) -> list[str]:
        return [row["specialty"] for row in self._all("SELECT DISTINCT specialty FROM doctors ORDER BY specialty")]

    def doctors(self, specialty: str | None = None) -> list[dict]:
        if specialty:
            return self._all("SELECT * FROM doctors WHERE specialty = ? ORDER BY full_name", (specialty,))
        return self._all("SELECT * FROM doctors ORDER BY specialty, full_name")

    def doctor(self, doctor_id: int) -> dict | None:
        return self._one("SELECT * FROM doctors WHERE id = ?", (doctor_id,))

    def search_doctors(self, text: str) -> list[dict]:
        # фильтрация в Python: LOWER() в SQLite не работает с кириллицей
        text = text.lower()
        return [d for d in self.doctors() if text in d["full_name"].lower() or text in d["specialty"].lower()]

    def patient_by_telegram(self, telegram_id: int) -> dict | None:
        return self._one("SELECT * FROM patients WHERE telegram_id = ?", (telegram_id,))

    def create_patient(self, telegram_id: int, full_name: str, phone: str) -> dict:
        cursor = self.db.execute("INSERT INTO patients (telegram_id, full_name, phone) VALUES (?, ?, ?)",
                                 (telegram_id, full_name, phone))
        self.db.commit()
        return self._one("SELECT * FROM patients WHERE id = ?", (cursor.lastrowid,))

    def busy_times(self, doctor_id: int, date: str) -> set[str]:
        rows = self._all("SELECT time FROM appointments WHERE doctor_id = ? AND date = ? AND status != 'cancelled'",
                         (doctor_id, date))
        return {row["time"] for row in rows}

    def create_appointment(self, patient_id: int, doctor_id: int, date: str, time: str, complaint: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO appointments (patient_id, doctor_id, date, time, complaint) VALUES (?, ?, ?, ?, ?)",
            (patient_id, doctor_id, date, time, complaint))
        self.db.commit()
        return cursor.lastrowid

    def appointment(self, appointment_id: int) -> dict | None:
        return self._one(
            "SELECT a.*, d.full_name AS doctor, d.specialty, d.cabinet FROM appointments a "
            "JOIN doctors d ON d.id = a.doctor_id WHERE a.id = ?", (appointment_id,))

    def patient_appointments(self, patient_id: int, statuses: tuple[str, ...]) -> list[dict]:
        marks = ",".join("?" * len(statuses))
        return self._all(
            "SELECT a.*, d.full_name AS doctor, d.specialty, d.cabinet, "
            "(SELECT group_concat(code || ' ' || title, '; ') FROM diagnoses WHERE appointment_id = a.id) AS diagnosis "
            f"FROM appointments a JOIN doctors d ON d.id = a.doctor_id WHERE a.patient_id = ? AND a.status IN ({marks}) "
            "ORDER BY a.date, a.time", (patient_id, *statuses))

    def update_appointment(self, appointment_id: int, **fields) -> None:
        sets = ", ".join(f"{key} = ?" for key in fields)
        self.db.execute(f"UPDATE appointments SET {sets} WHERE id = ?", (*fields.values(), appointment_id))
        self.db.commit()

    def delete_appointment(self, appointment_id: int) -> None:
        self.db.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        self.db.commit()

    def counts(self) -> dict:
        return {table: self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("doctors", "patients", "appointments", "diagnoses")}
