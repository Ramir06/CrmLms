-- Исправляем поле color_status в таблице attendance_attendancerecord
-- Сначала удаляем ограничение NOT NULL (если оно есть)
ALTER TABLE attendance_attendancerecord 
ALTER COLUMN color_status DROP NOT NULL;

-- Обновляем NULL значения на пустую строку
UPDATE attendance_attendancerecord 
SET color_status = '' 
WHERE color_status IS NULL;

-- Устанавливаем значение по умолчанию
ALTER TABLE attendance_attendancerecord 
ALTER COLUMN color_status SET DEFAULT '';

-- Возвращаем ограничение NOT NULL
ALTER TABLE attendance_attendancerecord 
ALTER COLUMN color_status SET NOT NULL;
