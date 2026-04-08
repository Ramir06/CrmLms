import os
import sys
from pathlib import Path

# Устанавливаем путь к проекту
project_path = r"c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms"
sys.path.insert(0, project_path)
os.chdir(project_path)

# Загружаем .env файл
env_path = Path(project_path).parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Импортируем Django после установки пути
import django
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # Применяем миграции
    print("Применяем миграции для attendance...")
    execute_from_command_line(['manage.py', 'migrate', 'attendance'])
    
    print("Применяем миграции для mentors...")
    execute_from_command_line(['manage.py', 'migrate', 'mentors'])
    
    print("Миграции успешно применены!")
