-- 1. SELECT: все врачи
SELECT * FROM doctors;

-- 2. WHERE: свободные записи
SELECT id, doctor_id, date, time FROM appointments WHERE status = 'free';

-- 3. ORDER BY: записи по дате и времени
SELECT id, date, time, status FROM appointments ORDER BY date, time;

-- 4. JOIN: записи с ФИО врача и пациента
SELECT a.id, a.date, a.time, d.full_name AS doctor, p.full_name AS patient
FROM appointments a
JOIN doctors d ON d.id = a.doctor_id
JOIN patients p ON p.id = a.patient_id;

-- 5. LEFT JOIN: все записи, в т. ч. свободные (без пациента)
SELECT a.id, a.date, a.time, COALESCE(p.full_name, '— свободно —') AS patient
FROM appointments a LEFT JOIN patients p ON p.id = a.patient_id;

-- 6. GROUP BY + 8. COUNT: количество записей у каждого врача
SELECT d.full_name, COUNT(a.id) AS total
FROM doctors d LEFT JOIN appointments a ON a.doctor_id = d.id
GROUP BY d.id;

-- 7. HAVING: врачи, у которых больше двух записей
SELECT doctor_id, COUNT(*) AS total FROM appointments GROUP BY doctor_id HAVING COUNT(*) > 2;

-- 9. SUM: стоимость услуг по каждому приёму
SELECT a.id, SUM(s.price * aps.quantity) AS cost
FROM appointments a
JOIN appointment_services aps ON aps.appointment_id = a.id
JOIN services s ON s.id = aps.service_id
GROUP BY a.id;

-- 10. INSERT: новый свободный слот
INSERT INTO appointments (doctor_id, date, time, status) VALUES (3, '2026-10-24', '15:00', 'free');

-- 11. UPDATE: запись пациента на свободный слот
UPDATE appointments SET patient_id = 5, status = 'booked' WHERE id = 3 AND status = 'free';

-- 12. DELETE: удаление отменённых записей
DELETE FROM appointments WHERE status = 'cancelled';

-- 13. Подзапрос: пациенты, у которых были завершённые приёмы
SELECT full_name FROM patients
WHERE id IN (SELECT patient_id FROM appointments WHERE status = 'completed');

-- 14. Несколько условий: свободные записи терапевтов 22.10.2026
SELECT a.* FROM appointments a JOIN doctors d ON d.id = a.doctor_id
WHERE a.status = 'free' AND d.specialty = 'терапевт' AND a.date = '2026-10-22';

-- 15. Связь нескольких таблиц: отделение → врач → приём → услуги
SELECT dep.name AS department, d.full_name, a.date, s.name AS service, aps.quantity
FROM departments dep
JOIN doctors d ON d.department_id = dep.id
JOIN appointments a ON a.doctor_id = d.id
JOIN appointment_services aps ON aps.appointment_id = a.id
JOIN services s ON s.id = aps.service_id
ORDER BY dep.name, a.date;

-- 16. AVG: средняя цена услуги
SELECT AVG(price) AS avg_price FROM services;
