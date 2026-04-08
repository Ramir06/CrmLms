-- КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ В PSQL (копируйте по одной)

-- 1. Изменить пароль пользователя postgres
ALTER USER postgres PASSWORD 'postgres';

-- 2. Проверить текущего пользователя
SELECT current_user;

-- 3. Создать базу данных если не существует
CREATE DATABASE crm_lms_db;

-- 4. Проверить базы данных
\l

-- 5. Выйти из psql
\q
