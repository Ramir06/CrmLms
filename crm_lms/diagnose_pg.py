#!/usr/bin/env python
"""Диагностика PostgreSQL аутентификации"""
import os
import sys
from pathlib import Path
import psycopg

# Загрузка .env с очисткой
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

print("=== Диагностика PostgreSQL ===")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")
print(f"DB_USER: {os.environ.get('DB_USER')}")
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_PORT: {os.environ.get('DB_PORT')}")

print("\n=== Тест 1: Подключение без указания базы данных ===")
try:
    # Подключаемся к postgres по умолчанию
    conn = psycopg.connect(
        dbname='postgres',  # База данных по умолчанию
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    )
    print("✅ Подключение к postgres успешно!")
    
    # Проверяем существование целевой базы данных
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (os.environ.get('DB_NAME'),))
    if cursor.fetchone():
        print(f"✅ База данных '{os.environ.get('DB_NAME')}' существует")
    else:
        print(f"❌ База данных '{os.environ.get('DB_NAME')}' НЕ существует")
        print("Создаем базу данных...")
        
        # Создаем базу данных
        cursor.execute(f'CREATE DATABASE "{os.environ.get("DB_NAME")}"')
        print(f"✅ База данных '{os.environ.get('DB_NAME')}' создана")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка подключения к postgres: {e}")

print("\n=== Тест 2: Подключение к целевой базе данных ===")
try:
    conn = psycopg.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    )
    print("✅ Подключение к целевой базе данных успешно!")
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка подключения к целевой базе: {e}")

print("\n=== Тест 3: Проверка прав пользователя ===")
try:
    conn = psycopg.connect(
        dbname='postgres',
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT current_user, current_database()")
    user, db = cursor.fetchone()
    print(f"Текущий пользователь: {user}")
    print(f"Текущая база данных: {db}")
    
    # Проверяем права на создание баз данных
    cursor.execute("SELECT has_database_privilege(current_user, 'createdb')")
    can_create = cursor.fetchone()[0]
    print(f"Права на создание БД: {can_create}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка проверки прав: {e}")

print("\n=== Рекомендации ===")
print("1. Если база данных не существует - создайте ее:")
print(f"   CREATE DATABASE \"{os.environ.get('DB_NAME')}\";")
print("2. Если пользователь не имеет прав - используйте суперпользователя:")
print("   ALTER USER postgres WITH SUPERUSER;")
print("3. Проверьте пароль пользователя postgres")
print("4. Убедитесь что PostgreSQL принимает подключения с 127.0.0.1")
