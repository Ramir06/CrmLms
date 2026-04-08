#!/usr/bin/env python
"""Исправление подключения к PostgreSQL - разные хосты и методы"""
import os
import sys
from pathlib import Path
import psycopg

# Загрузка .env
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'

with open(env_path, 'rb') as f:
    raw = f.read()
content = raw.decode('utf-8')

for line in content.split('\n'):
    line = line.strip().replace('\r', '').replace('\n', '')
    if line and '=' in line:
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip()

db_params = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': os.environ.get('DB_PORT'),
}

print("=== Тест разных хостов ===")

hosts = ['localhost', '127.0.0.1', 'localhost.localdomain', '::1']

for host in hosts:
    print(f"\n--- Тест хоста: {host} ---")
    try:
        conn = psycopg.connect(host=host, **db_params)
        print(f"✅ Подключение успешно к {host}!")
        conn.close()
        break
    except Exception as e:
        print(f"❌ {host}: {e}")

print("\n=== Тест с разными базами данных ===")
databases = ['postgres', 'template1', 'template0', os.environ.get('DB_NAME')]

for db in databases:
    print(f"\n--- Тест базы данных: {db} ---")
    try:
        conn = psycopg.connect(
            host='localhost',
            dbname=db,
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            port=os.environ.get('DB_PORT')
        )
        print(f"✅ Подключение успешно к {db}!")
        
        # Если подключились к postgres, создаем целевую базу
        if db in ['postgres', 'template1'] and db != os.environ.get('DB_NAME'):
            cursor = conn.cursor()
            try:
                cursor.execute(f'CREATE DATABASE "{os.environ.get("DB_NAME")}"')
                print(f"✅ База данных {os.environ.get('DB_NAME')} создана!")
                conn.commit()
            except Exception as create_error:
                print(f"База данных уже существует или ошибка: {create_error}")
            finally:
                cursor.close()
        
        conn.close()
        break
    except Exception as e:
        print(f"❌ {db}: {e}")

print("\n=== Тест с trust аутентификацией ===")
try:
    # Пробуем без пароля (если настроен trust)
    conn = psycopg.connect(
        host='localhost',
        dbname='postgres',
        user='postgres',
        port=os.environ.get('DB_PORT')
    )
    print("✅ Подключение без пароля успешно!")
    conn.close()
except Exception as e:
    print(f"❌ Без пароля: {e}")

print("\n=== Проверка переменных окружения PostgreSQL ===")
pg_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGDATABASE', 'PGPASSWORD', 'PGCLIENTENCODING']
for var in pg_vars:
    value = os.environ.get(var, 'не установлена')
    print(f"{var}: {repr(value)}")

print("\n=== Рекомендации по исправлению ===")
print("1. Измените DB_HOST в .env с '127.0.0.1' на 'localhost'")
print("2. Проверьте пароль postgres в PostgreSQL")
print("3. Попробуйте подключиться через psql:")
print("   psql -h localhost -U postgres")
print("4. Проверьте pg_hba.conf для настройки аутентификации")
print("5. Перезапустите PostgreSQL сервис")

# Создаем исправленный .env с localhost
print("\n=== Создание исправленного .env ===")
env_content = f"""SECRET_KEY=django-insecure-dev-key-change-in-production-12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME={os.environ.get('DB_NAME')}
DB_USER={os.environ.get('DB_USER')}
DB_PASSWORD={os.environ.get('DB_PASSWORD')}
DB_HOST=localhost
DB_PORT={os.environ.get('DB_PORT')}
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=mirayana.baekova@gmail.com
EMAIL_HOST_PASSWORD=nrutgpbvoiqoulfq
DEFAULT_FROM_EMAIL=mirayana.baekova@gmail.com
"""

print("Новый .env (с localhost вместо 127.0.0.1):")
print(env_content)
