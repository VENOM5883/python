"""Repository на SQLite."""
import sqlite3
from datetime import datetime

from src.models.entities import Appointment, AppointmentStatus, Doctor, Patient

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, phone TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS doctors (id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, specialty TEXT NOT NULL,
                                    slot_minutes INTEGER NOT NULL DEFAULT 30);
CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id), doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    start TEXT NOT NULL, status TEXT NOT NULL);
"""


class ClinicRepository:
    def __init__(self, path: str = ":memory:") -> None:
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    # пациенты
    def add_patient(self, patient: Patient) -> Patient:
        cursor = self.db.execute("INSERT INTO patients (full_name, phone) VALUES (?, ?)",
                                 (patient.full_name, patient.phone))
        self.db.commit()
        patient.id = cursor.lastrowid
        return patient

    def get_patient(self, patient_id: int) -> Patient | None:
        row = self.db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        return Patient(**dict(row)) if row else None

    def find_patient_by_phone(self, phone: str) -> Patient | None:
        row = self.db.execute("SELECT * FROM patients WHERE phone = ?", (phone,)).fetchone()
        return Patient(**dict(row)) if row else None

    # врачи
    def add_doctor(self, doctor: Doctor) -> Doctor:
        cursor = self.db.execute("INSERT INTO doctors (full_name, specialty, slot_minutes) VALUES (?, ?, ?)",
                                 (doctor.full_name, doctor.specialty, doctor.slot_minutes))
        self.db.commit()
        doctor.id = cursor.lastrowid
        return doctor

    def get_doctor(self, doctor_id: int) -> Doctor | None:
        row = self.db.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
        return Doctor(**dict(row)) if row else None

    def doctors_by_specialty(self, specialty: str) -> list[Doctor]:
        rows = self.db.execute("SELECT * FROM doctors WHERE specialty = ? ORDER BY full_name", (specialty,))
        return [Doctor(**dict(r)) for r in rows]

    # записи
    @staticmethod
    def _to_appointment(row) -> Appointment:
        return Appointment(row["id"], row["patient_id"], row["doctor_id"], datetime.fromisoformat(row["start"]),
                           AppointmentStatus(row["status"]))

    def add_appointment(self, appointment: Appointment) -> Appointment:
        cursor = self.db.execute(
            "INSERT INTO appointments (patient_id, doctor_id, start, status) VALUES (?, ?, ?, ?)",
            (appointment.patient_id, appointment.doctor_id, appointment.start.isoformat(), appointment.status.value))
        self.db.commit()
        appointment.id = cursor.lastrowid
        return appointment

    def get_appointment(self, appointment_id: int) -> Appointment | None:
        row = self.db.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,)).fetchone()
        return self._to_appointment(row) if row else None

    def update_status(self, appointment_id: int, status: AppointmentStatus) -> None:
        self.db.execute("UPDATE appointments SET status = ? WHERE id = ?", (status.value, appointment_id))
        self.db.commit()

    def doctor_appointments(self, doctor_id: int, day: str) -> list[Appointment]:
        rows = self.db.execute("SELECT * FROM appointments WHERE doctor_id = ? AND start LIKE ? AND status = ?",
                               (doctor_id, f"{day}%", AppointmentStatus.BOOKED.value))
        return [self._to_appointment(r) for r in rows]

    def patient_appointments(self, patient_id: int) -> list[Appointment]:
        rows = self.db.execute("SELECT * FROM appointments WHERE patient_id = ? ORDER BY start", (patient_id,))
        return [self._to_appointment(r) for r in rows]
