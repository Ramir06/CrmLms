-- Добавляем поле per_lesson_rate в таблицу mentors_mentorprofile
ALTER TABLE mentors_mentorprofile 
ADD COLUMN per_lesson_rate DECIMAL(10, 2) DEFAULT 0.00 NOT NULL;

-- Обновляем типы зарплат для добавления нового варианта
-- Это не требует изменений в базе данных, так как это только choices в Django
