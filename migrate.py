import os
import sys
import django

# Устанавливаем путь к Django проекту
sys.path.append(r'c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms')
os.chdir(r'c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Инициализируем Django
django.setup()

from django.core.management import execute_from_command_line

# Применяем миграции
execute_from_command_line(['manage.py', 'migrate'])

print("Миграции успешно применены!")
