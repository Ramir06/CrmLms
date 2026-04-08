#!/usr/bin/env python
"""Тест подключения к PostgreSQL вне Django"""
import os
import sys
from pathlib import Path
import environ

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    import psycopg2
    print("✅ psycopg2 импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта psycopg2: {e}")
    sys.exit(1)

# Загрузка .env как в Django
print("\n=== Загрузка .env файла ===")
env = environ.Env()
env_file = BASE_DIR / '.env'

if env_file.exists():
    print(f"✅ Файл .env найден: {env_file}")
    
    # Читаем .env файл вручную для отладки
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    print(f"Содержимое .env (первые 200 символов): {repr(env_content[:200])}")
    
    # Загружаем через environ
    environ.Env.read_env(env_file)
    print("✅ .env загружен через environ.Env.read_env()")
else:
    print(f"❌ Файл .env не найден: {env_file}")
    sys.exit(1)

print("\n=== Переменные окружения ===")
db_vars = {
    'DB_NAME': env('DB_NAME', default=''),
    'DB_USER': env('DB_USER', default=''),
    'DB_PASSWORD': env('DB_PASSWORD', default=''),
    'DB_HOST': env('DB_HOST', default=''),
    'DB_PORT': env('DB_PORT', default=''),
}

for key, value in db_vars.items():
    print(f"{key}: {repr(value)} (len: {len(value)})")
    if '\r' in value or '\n' in value:
        print(f"  ⚠️ ВНИМАНИЕ: Перенос строки в {key}!")

print("\n=== Тест подключения к PostgreSQL ===")

# Проверяем наличие всех переменных
missing_vars = [k for k, v in db_vars.items() if not v]
if missing_vars:
    print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
    sys.exit(1)

try:
    # Очищаем переменные от \r\n
    clean_vars = {k: v.strip().replace('\r', '').replace('\n', '') for k, v in db_vars.items()}
    
    print("Очищенные переменные:")
    for key, value in clean_vars.items():
        print(f"{key}: {repr(value)}")
    
    print("\nПопытка подключения...")
    
    conn = psycopg2.connect(
        dbname=clean_vars['DB_NAME'],
        user=clean_vars['DB_USER'],
        password=clean_vars['DB_PASSWORD'],
        host=clean_vars['DB_HOST'],
        port=clean_vars['DB_PORT']
    )
    
    print("✅ Подключение к PostgreSQL успешно!")
    
    # Тестовый запрос
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"Версия PostgreSQL: {version}")
    
    cursor.close()
    conn.close()
    print("✅ Соединение закрыто корректно")
    
except psycopg2.OperationalError as e:
    print(f"❌ Ошибка подключения: {e}")
    print("\nВозможные причины:")
    print("- PostgreSQL сервер не запущен")
    print("- Неверные учетные данные")
    print("- База данных не существует")
    print("- Неверный хост/порт")
    print("- Проблема с кодировкой символов в пароле")
    
except Exception as e:
    print(f"❌ Неожиданная ошибка: {type(e).__name__}: {e}")

print("\n=== Дополнительная информация ===")
print(f"Python версия: {sys.version}")
print(f"psycopg2 версия: {psycopg2.__version__}")

# Проверка системных переменных
print("\nСистемные переменные PG:")
pg_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGDATABASE', 'PGPASSWORD']
for var in pg_vars:
    value = os.environ.get(var, 'не установлена')
    print(f"{var}: {repr(value)}")
