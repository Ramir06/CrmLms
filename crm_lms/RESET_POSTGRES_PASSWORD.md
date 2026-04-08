# ИНСТРУКЦИЯ: Сброс пароля PostgreSQL на Windows

## Проблема
Пользователь postgres не может аутентифицироваться. Нужно сбросить пароль.

## Решение 1: Сброс пароля postgres

### Шаг 1: Остановить PostgreSQL сервис
```cmd
net stop postgresql-x64-18
```

### Шаг 2: Найти pg_hba.conf
Файл находится в: `C:\Program Files\PostgreSQL\18\data\pg_hba.conf`

### Шаг 3: Изменить метод аутентификации
В pg_hba.conf найдите строки для localhost и измените:
```
# Было:
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# Стало:
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
```

### Шаг 4: Запустить PostgreSQL
```cmd
net start postgresql-x64-18
```

### Шаг 5: Подключиться и сменить пароль
```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

В psql выполните:
```sql
ALTER USER postgres PASSWORD 'postgres';
\q
```

### Шаг 6: Восстановить md5 аутентификацию
В pg_hba.conf верните:
```
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

### Шаг 7: Перезапустить PostgreSQL
```cmd
net stop postgresql-x64-18
net start postgresql-x64-18
```

## Решение 2: Создание нового пользователя (альтернатива)

Если не хотите менять пароль postgres:

### Шаг 1: Подключиться как postgres (с trust как выше)
```cmd
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

### Шаг 2: Создать нового пользователя
```sql
CREATE USER django_user WITH PASSWORD 'django_pass';
CREATE DATABASE crm_lms_db OWNER django_user;
GRANT ALL PRIVILEGES ON DATABASE crm_lms_db TO django_user;
\q
```

### Шаг 3: Обновить .env
```
DB_USER=django_user
DB_PASSWORD=django_pass
```

## Автоматический скрипт для сброса пароля

```python
# reset_postgres_password.py
import os
import subprocess
import time

def reset_postgres_password():
    print("=== Сброс пароля PostgreSQL ===")
    
    # Шаг 1: Остановить сервис
    print("1. Остановка PostgreSQL...")
    subprocess.run(['net', 'stop', 'postgresql-x64-18'], capture_output=True)
    time.sleep(3)
    
    # Шаг 2: Изменить pg_hba.conf
    pg_hba_path = r"C:\Program Files\PostgreSQL\18\data\pg_hba.conf"
    print(f"2. Изменение {pg_hba_path}...")
    
    # Читаем файл
    with open(pg_hba_path, 'r') as f:
        content = f.read()
    
    # Меняем md5 на trust
    content = content.replace('md5', 'trust')
    
    # Записываем обратно
    with open(pg_hba_path, 'w') as f:
        f.write(content)
    
    # Шаг 3: Запустить сервис
    print("3. Запуск PostgreSQL...")
    subprocess.run(['net', 'start', 'postgresql-x64-18'], capture_output=True)
    time.sleep(5)
    
    # Шаг 4: Сменить пароль
    print("4. Установка нового пароля...")
    psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
    
    result = subprocess.run([
        psql_path, '-U', 'postgres', '-h', 'localhost',
        '-c', "ALTER USER postgres PASSWORD 'postgres';"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Пароль успешно изменен на 'postgres'")
    else:
        print(f"❌ Ошибка: {result.stderr}")
    
    # Шаг 5: Восстановить md5
    print("5. Восстановление md5 аутентификации...")
    with open(pg_hba_path, 'r') as f:
        content = f.read()
    
    content = content.replace('trust', 'md5')
    
    with open(pg_hba_path, 'w') as f:
        f.write(content)
    
    # Шаг 6: Перезапустить
    print("6. Перезапуск PostgreSQL...")
    subprocess.run(['net', 'stop', 'postgresql-x64-18'], capture_output=True)
    time.sleep(3)
    subprocess.run(['net', 'start', 'postgresql-x64-18'], capture_output=True)
    time.sleep(5)
    
    print("✅ Сброс пароля завершен!")

if __name__ == "__main__":
    reset_postgres_password()
```

## Проверка после сброса

После сброса пароля проверьте подключение:

```python
# test_after_reset.py
import psycopg

try:
    conn = psycopg.connect(
        host='localhost',
        user='postgres',
        password='postgres',
        dbname='postgres',
        port='5432'
    )
    print("✅ Подключение успешно!")
    
    # Создать базу данных если нужно
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'crm_lms_db'")
    if not cursor.fetchone():
        cursor.execute("CREATE DATABASE crm_lms_db")
        print("✅ База данных crm_lms_db создана")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
```

## Финальный .env файл

```
SECRET_KEY=django-insecure-dev-key-change-in-production-12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=crm_lms_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=mirayana.baekova@gmail.com
EMAIL_HOST_PASSWORD=nrutgpbvoiqoulfq
DEFAULT_FROM_EMAIL=mirayana.baekova@gmail.com
```

## Запуск Django после исправления

```cmd
cd crm_lms
python manage.py runserver
```

Теперь Django должен успешно запуститься!
