-- Лабораторная работа №11, вариант 15: медицинская клиника
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE,
    floor   INTEGER NOT NULL CHECK (floor BETWEEN 1 AND 10)
);

CREATE TABLE IF NOT EXISTS doctors (
    id            INTEGER PRIMARY KEY,
    full_name     TEXT NOT NULL,
    specialty     TEXT NOT NULL,
    cabinet       INTEGER NOT NULL CHECK (cabinet > 0),
    photo         TEXT,                                  -- путь к фото на CDN
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS patients (
    id         INTEGER PRIMARY KEY,
    full_name  TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    phone      TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS appointments (                -- основная сущность
    id         INTEGER PRIMARY KEY,
    doctor_id  INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    patient_id INTEGER REFERENCES patients(id) ON DELETE SET NULL,
    date       TEXT NOT NULL,
    time       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'free'
               CHECK (status IN ('free', 'booked', 'completed', 'cancelled')),
    UNIQUE (doctor_id, date, time)
);

CREATE TABLE IF NOT EXISTS services (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE,
    price REAL NOT NULL CHECK (price >= 0)
);

-- Связь N:M «приём — оказанные услуги»
CREATE TABLE IF NOT EXISTS appointment_services (
    appointment_id INTEGER NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    service_id     INTEGER NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
    quantity       INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    PRIMARY KEY (appointment_id, service_id)
);

-- Индексы
-- 1) расписание врача на дату: WHERE doctor_id = ? AND date = ?
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, date);
-- 2) поиск свободных записей: WHERE status = 'free'
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
-- 3) поиск врачей по специальности
CREATE INDEX IF NOT EXISTS idx_doctors_specialty ON doctors(specialty);
