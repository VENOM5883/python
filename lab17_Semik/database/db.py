"""SQLite: схема и учебные данные (все данные вымышленные)."""
import sqlite3

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, specialty TEXT NOT NULL,
    cabinet INTEGER NOT NULL, experience INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY, telegram_id INTEGER UNIQUE, full_name TEXT NOT NULL, phone TEXT);
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    date TEXT NOT NULL, time TEXT NOT NULL, complaint TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','completed','cancelled')),
    UNIQUE (doctor_id, date, time));
CREATE TABLE IF NOT EXISTS diagnoses (
    id INTEGER PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    code TEXT NOT NULL, title TEXT NOT NULL);
"""

DOCTORS = [("Смирнова Елена Викторовна", "терапевт", 101, 12), ("Громов Артём Сергеевич", "терапевт", 102, 5),
           ("Кузнецов Олег Петрович", "кардиолог", 205, 20), ("Орлова Наталья Андреевна", "невролог", 310, 9),
           ("Белова Мария Игоревна", "окулист", 120, 7), ("Зайцев Игорь Львович", "хирург", 402, 15)]
PATIENTS = [(None, "Иванов Иван Иванович", "+79001112233"), (None, "Петрова Анна Сергеевна", "+79002223344"),
            (None, "Сидоров Павел Олегович", "+79003334455")]
APPOINTMENTS = [
    (1, 1, "2026-10-01", "09:00", "Кашель", "completed"), (1, 3, "2026-10-05", "10:00", "Давление", "completed"),
    (2, 4, "2026-10-07", "12:00", "Головная боль", "completed"), (3, 5, "2026-10-08", "14:00", "Зрение", "completed"),
    (2, 1, "2026-10-10", "09:30", "Температура", "cancelled"), (3, 2, "2026-10-12", "11:00", "Слабость", "completed"),
    (1, 6, "2026-10-14", "15:00", "Боль в спине", "completed"),
    (2, 3, "2026-10-21", "10:00", "Контроль ЭКГ", "planned"), (3, 1, "2026-10-22", "09:00", "Осмотр", "planned"),
]
DIAGNOSES = [(1, "J06.9", "ОРВИ"), (2, "I10", "Гипертоническая болезнь"), (3, "G43.9", "Мигрень"),
             (4, "H52.1", "Миопия"), (6, "R53", "Астения"), (7, "M54.5", "Люмбалгия")]


def connect(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    if connection.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
        connection.executemany("INSERT INTO doctors (full_name, specialty, cabinet, experience) VALUES (?,?,?,?)", DOCTORS)
        connection.executemany("INSERT INTO patients (telegram_id, full_name, phone) VALUES (?,?,?)", PATIENTS)
        connection.executemany("INSERT INTO appointments (patient_id, doctor_id, date, time, complaint, status) "
                               "VALUES (?,?,?,?,?,?)", APPOINTMENTS)
        connection.executemany("INSERT INTO diagnoses (appointment_id, code, title) VALUES (?,?,?)", DIAGNOSES)
    connection.commit()
