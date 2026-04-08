#!/usr/bin/env python
"""Тестирование различных подходов к решению проблемы psycopg2"""
import os
import sys
from pathlib import Path

# Установка переменных окружения с очисткой
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'

# Очистка и загрузка .env
with open(env_path, 'rb') as f:
    raw = f.read()

try:
    content = raw.decode('utf-8')
except UnicodeDecodeError:
    content = raw.decode('latin-1')

for line in content.split('\n'):
    line = line.strip().replace('\r', '').replace('\n', '')
    if line and '=' in line:
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip()

print("=== Тест 1: Прямой psycopg2 с очисткой ===")
try:
    import psycopg2
    
    # Получаем очищенные переменные
    db_params = {
        'dbname': os.environ.get('DB_NAME', 'crm_lms_db'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'postgres'),
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '5432'),
    }
    
    print(f"Параметры подключения: {db_params}")
    
    # Пробуем подключиться
    conn = psycopg2.connect(**db_params)
    print("✅ Прямое подключение успешно!")
    conn.close()
    
except Exception as e:
    print(f"❌ Прямое подключение не удалось: {e}")

print("\n=== Тест 2: psycopg2 с DSN строкой ===")
try:
    import psycopg2
    
    # Создаем DSN строку вручную
    dsn = f"dbname={os.environ.get('DB_NAME')} user={os.environ.get('DB_USER')} password={os.environ.get('DB_PASSWORD')} host={os.environ.get('DB_HOST')} port={os.environ.get('DB_PORT')}"
    
    print(f"DSN: {dsn}")
    
    conn = psycopg2.connect(dsn)
    print("✅ Подключение через DSN успешно!")
    conn.close()
    
except Exception as e:
    print(f"❌ Подключение через DSN не удалось: {e}")

print("\n=== Тест 3: psycopg2 с разными кодировками ===")
try:
    import psycopg2
    
    # Принудительно устанавливаем кодировку
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
        client_encoding='UTF8'
    )
    print("✅ Подключение с client_encoding успешно!")
    conn.close()
    
except Exception as e:
    print(f"❌ Подключение с client_encoding не удалось: {e}")

print("\n=== Тест 4: Проверка версии psycopg2 и PostgreSQL ===")
try:
    import psycopg2
    print(f"psycopg2 версия: {psycopg2.__version__}")
    
    # Пробуем получить версию PostgreSQL
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
        connect_timeout=5
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"PostgreSQL версия: {version}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Проверка версии не удалась: {e}")

print("\n=== Тест 5: Альтернативный библиотеки ===")
try:
    import psycopg2.extras
    print("✅ psycopg2.extras доступен")
except ImportError as e:
    print(f"❌ psycopg2.extras недоступен: {e}")

# Проверка наличия альтернативных драйверов
try:
    import psycopg
    print("✅ psycopg (psycopg3) доступен")
except ImportError:
    print("❌ psycopg (psycopg3) недоступен")

print("\n=== Системная информация ===")
print(f"Python версия: {sys.version}")
print(f"ОС: {os.name}")

# Проверка переменных окружения PostgreSQL
pg_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGDATABASE', 'PGPASSWORD', 'PGCLIENTENCODING']
for var in pg_vars:
    value = os.environ.get(var, 'не установлена')
    print(f"{var}: {repr(value)}")
