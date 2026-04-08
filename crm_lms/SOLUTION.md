# ИТОГОВОЕ РЕШЕНИЕ: Исправление UnicodeDecodeError в Django + PostgreSQL

## Проблема
`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2 ... (ошибка возникает при psycopg2.connect)`

## Корневая причина
1. **Windows перенос строки (\r\n)** в .env файле
2. **Несовместимость psycopg2 с Python 3.13 на Windows**
3. **Отсутствие очистки переменных окружения**

## Решение 1: Исправление .env и загрузки (Рекомендуется)

### 1.1 Очистка .env файла
```bash
# Конвертировать Windows переносы строк в Unix
python -c "
import os
from pathlib import Path
env_path = Path('.env')
with open(env_path, 'rb') as f:
    content = f.read().decode('utf-8')
cleaned = content.replace('\r\n', '\n').replace('\r', '\n')
with open(env_path, 'w', encoding='utf-8') as f:
    f.write(cleaned)
print('.env очищен от Windows переносов строк')
"
```

### 1.2 Безопасная загрузка в settings.py
```python
# config/settings/base.py
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Безопасная загрузка .env с очисткой от Windows символов
def load_env_cleanly(env_path):
    """Загружает .env файл с полной очисткой от проблемных символов"""
    if not env_path.exists():
        return
    
    with open(env_path, 'rb') as f:
        raw_content = f.read()
    
    try:
        content = raw_content.decode('utf-8')
    except UnicodeDecodeError:
        content = raw_content.decode('latin-1')
    
    for line in content.split('\n'):
        line = line.strip().replace('\r', '').replace('\n', '')
        if line and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

# Загружаем .env с очисткой
load_env_cleanly(BASE_DIR / '.env')

env = environ.Env(DEBUG=(bool, False))

# Настройки базы данных с очисткой
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='crm_lms_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}
```

## Решение 2: Переход на psycopg3 (Альтернатива)

### 2.1 Установка psycopg3
```bash
pip uninstall psycopg2-binary
pip install psycopg psycopg-binary
```

### 2.2 Настройка Django для psycopg3
```python
# config/settings/base.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='crm_lms_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            # psycopg3 автоматически используется, но можно явно указать
        }
    }
}
```

## Решение 3: Проверка PostgreSQL сервера

### 3.1 Проверка статуса PostgreSQL
```bash
# Windows
net start postgresql-x64-13  # или ваша версия

# или через PowerShell
Get-Service postgresql*
```

### 3.2 Тест подключения вне Django
```python
# test_pg_connection.py
import os
import psycopg2  # или psycopg
from pathlib import Path

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

# Тест подключения
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    )
    print("✅ PostgreSQL подключение успешно!")
    conn.close()
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
```

## Диагностика проблем

### Пошаговая проверка:
1. **Проверить .env файл:**
   ```bash
   python check_env.py
   ```

2. **Проверить переменные окружения:**
   ```bash
   python load_env_clean.py
   ```

3. **Тестировать psycopg2/psycopg3:**
   ```bash
   python debug_psycopg2.py
   python test_psycopg3.py
   ```

4. **Запустить Django с отладкой:**
   ```bash
   python manage.py runserver --noreload
   ```

## Альтернативные причины

Если проблема не решена:

1. **Версия Python:** psycopg2 может быть несовместим с Python 3.13
   ```bash
   # Понизить версию Python до 3.11-3.12
   ```

2. **Системные переменные Windows:**
   ```cmd
   set PGCLIENTENCODING=UTF8
   set PYTHONIOENCODING=utf-8
   ```

3. **Поврежденный psycopg2:**
   ```bash
   pip uninstall psycopg2-binary
   pip install --no-cache-dir psycopg2-binary
   ```

4. **Проблемы с PostgreSQL:**
   - Проверить, что сервер запущен
   - Проверить кодировку базы данных (должна быть UTF8)
   - Проверить права пользователя postgres

## Минимальный тест-код (test_pg.py)

```python
#!/usr/bin/env python
import os
import psycopg2
from pathlib import Path

# Загрузка и очистка .env
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

# Тест подключения
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    )
    print("✅ Подключение успешно!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    print(f"PostgreSQL: {cursor.fetchone()[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
```

## Рекомендации

1. **Использовать Решение 1** (очистка .env + безопасная загрузка)
2. **Если не помогло** - перейти на psycopg3 (Решение 2)
3. **Проверить PostgreSQL сервер** (Решение 3)
4. **Обновить requirements.txt:**
   ```
   psycopg2-binary==2.9.11  # или psycopg==3.3.3
   django-environ==0.11.2
   ```
