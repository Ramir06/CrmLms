#!/usr/bin/env python
"""Финальное решение проблемы с psycopg2 - патч на уровне библиотеки"""
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import extensions

# Очистка переменных окружения
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'

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

print("=== Решение 1: Патч psycopg2.connect ===")

# Сохраняем оригинальную функцию
original_connect = psycopg2.connect

def patched_connect(*args, **kwargs):
    """Патченная функция connect с обработкой Unicode ошибок"""
    try:
        return original_connect(*args, **kwargs)
    except UnicodeDecodeError as e:
        print(f"Перехват UnicodeDecodeError: {e}")
        
        # Если ошибка в параметрах, пробуем очистить их
        if kwargs:
            print("Очистка параметров подключения...")
            cleaned_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, str):
                    # Принудительная очистка от проблемных символов
                    cleaned_value = value.encode('utf-8', errors='ignore').decode('utf-8')
                    cleaned_kwargs[key] = cleaned_value
                    print(f"  {key}: {repr(value)} -> {repr(cleaned_value)}")
                else:
                    cleaned_kwargs[key] = value
            
            try:
                return original_connect(**cleaned_kwargs)
            except Exception as e2:
                print(f"Повторная ошибка после очистки: {e2}")
        
        # Если не помогло, пробуем с DSN
        if args:
            print("Пробуем с DSN строкой...")
            try:
                dsn = args[0]
                cleaned_dsn = dsn.encode('utf-8', errors='ignore').decode('utf-8')
                return original_connect(cleaned_dsn)
            except Exception as e3:
                print(f"Ошибка с DSN: {e3}")
        
        raise e

# Применяем патч
psycopg2.connect = patched_connect

print("=== Тест подключения с патчем ===")
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    )
    print("✅ Подключение успешно с патчем!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"PostgreSQL версия: {version}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Даже с патчем не удалось: {e}")

print("\n=== Решение 2: Установка кодировки клиента ===")
try:
    # Восстанавливаем оригинальную функцию
    psycopg2.connect = original_connect
    
    # Устанавливаем кодировку на уровне клиента
    os.environ['PGCLIENTENCODING'] = 'UTF8'
    
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
        client_encoding='UTF8'
    )
    print("✅ Подключение успешно с client_encoding!")
    conn.close()
    
except Exception as e:
    print(f"❌ С client_encoding не удалось: {e}")

print("\n=== Решение 3: Использование connection_string ===")
try:
    # Формируем connection string с экранированием
    params = {
        'dbname': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
    }
    
    # Создаем connection string
    conn_str = " ".join([f"{k}={v}" for k, v in params.items()])
    print(f"Connection string: {conn_str}")
    
    conn = psycopg2.connect(conn_str)
    print("✅ Подключение успешно через connection string!")
    conn.close()
    
except Exception as e:
    print(f"❌ Через connection string не удалось: {e}")

print("\n=== Рекомендации ===")
print("1. Переустановить psycopg2: pip uninstall psycopg2-binary && pip install psycopg2-binary")
print("2. Использовать psycopg3: pip install psycopg")
print("3. Проверить версию PostgreSQL и кодировку базы данных")
print("4. Установить переменную окружения PGCLIENTENCODING=UTF8")
