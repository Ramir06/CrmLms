#!/usr/bin/env python
"""Проверка и сброс пароля PostgreSQL через Windows"""
import os
import sys
import subprocess
from pathlib import Path

print("=== Проверка PostgreSQL через Windows ===")

# Путь к psql
psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"

if os.path.exists(psql_path):
    print(f"✅ psql найден: {psql_path}")
else:
    print(f"❌ psql не найден: {psql_path}")
    sys.exit(1)

print("\n=== Тест 1: Подключение с пустым паролем ===")
try:
    result = subprocess.run([
        psql_path, 
        "-U", "postgres", 
        "-h", "localhost",
        "-c", "SELECT current_user;"
    ], capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print("✅ Подключение без пароля успешно!")
        print("Вывод:", result.stdout)
    else:
        print(f"❌ Ошибка: {result.stderr}")
        
except Exception as e:
    print(f"❌ Исключение: {e}")

print("\n=== Тест 2: Подключение с паролем 'postgres' ===")
try:
    # Устанавливаем переменную PGPASSWORD
    env = os.environ.copy()
    env['PGPASSWORD'] = 'postgres'
    
    result = subprocess.run([
        psql_path, 
        "-U", "postgres", 
        "-h", "localhost",
        "-c", "SELECT current_user;"
    ], capture_output=True, text=True, timeout=10, env=env)
    
    if result.returncode == 0:
        print("✅ Подключение с паролем 'postgres' успешно!")
        print("Вывод:", result.stdout)
    else:
        print(f"❌ Ошибка: {result.stderr}")
        
except Exception as e:
    print(f"❌ Исключение: {e}")

print("\n=== Тест 3: Подключение с паролем '008400.s' ===")
try:
    env = os.environ.copy()
    env['PGPASSWORD'] = '008400.s'
    
    result = subprocess.run([
        psql_path, 
        "-U", "postgres", 
        "-h", "localhost",
        "-c", "SELECT current_user;"
    ], capture_output=True, text=True, timeout=10, env=env)
    
    if result.returncode == 0:
        print("✅ Подключение с паролем '008400.s' успешно!")
        print("Вывод:", result.stdout)
    else:
        print(f"❌ Ошибка: {result.stderr}")
        
except Exception as e:
    print(f"❌ Исключение: {e}")

print("\n=== Рекомендации ===")
print("1. Если ни один пароль не подошел - сбросьте пароль postgres:")
print("   - Остановите PostgreSQL сервис")
print("   - Запустите в безопасном режиме без аутентификации")
print("   - Подключитесь и установите новый пароль")
print("2. Или создайте нового пользователя:")
print("   CREATE USER django_user WITH PASSWORD 'django_pass';")
print("   GRANT ALL PRIVILEGES ON DATABASE crm_lms_db TO django_user;")

print("\n=== Создание .env с правильным паролем ===")
print("Если какой-то пароль сработал, обновите .env:")
print("DB_PASSWORD=postgres  # или другой рабочий пароль")
