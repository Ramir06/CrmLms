#!/usr/bin/env python
"""Тестирование psycopg3 как замены psycopg2"""
import os
import sys
from pathlib import Path

# Загрузка .env с очисткой
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'

with open(env_path, 'rb') as f:
    raw = f.read()

content = raw.decode('utf-8')  # Пробуем UTF-8

for line in content.split('\n'):
    line = line.strip().replace('\r', '').replace('\n', '')
    if line and '=' in line:
        key, value = line.split('=', 1)
        os.environ[key.strip()] = value.strip()

print("=== Тест psycopg3 ===")
try:
    import psycopg
    print(f"psycopg3 версия: {psycopg.__version__}")
    
    # Создаем connection string
    conn_params = {
        'dbname': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'), 
        'password': os.environ.get('DB_PASSWORD'),
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
    }
    
    print(f"Параметры: {conn_params}")
    
    # Подключаемся через psycopg3
    conn = psycopg.connect(**conn_params)
    print("✅ psycopg3 подключение успешно!")
    
    # Тестовый запрос
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"PostgreSQL версия: {version}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ psycopg3 ошибка: {e}")

print("\n=== Интеграция psycopg3 в Django ===")
print("Для использования psycopg3 в Django нужно:")
print("1. Установить psycopg: pip install psycopg")
print("2. Изменить DATABASES в settings.py:")
print("   'ENGINE': 'django.db.backends.postgresql',")
print("   # psycopg3 автоматически определится как драйвер")
print("3. Или явно указать:")
print("   'OPTIONS': {'driver': 'psycopg'}")

# Создадим тестовый Django settings с psycopg3
print("\n=== Тест Django с psycopg3 ===")
try:
    import django
    from django.conf import settings
    
    # Минимальная конфигурация Django
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': os.environ.get('DB_NAME'),
                    'USER': os.environ.get('DB_USER'),
                    'PASSWORD': os.environ.get('DB_PASSWORD'),
                    'HOST': os.environ.get('DB_HOST'),
                    'PORT': os.environ.get('DB_PORT'),
                    'OPTIONS': {
                        'driver': 'psycopg',  # Принудительно используем psycopg3
                    }
                }
            },
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            SECRET_KEY='test-key'
        )
    
    django.setup()
    
    # Тест подключения через Django
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ Django с psycopg3 работает! Результат: {result}")
        
except Exception as e:
    print(f"❌ Django с psycopg3 ошибка: {e}")
    import traceback
    traceback.print_exc()
