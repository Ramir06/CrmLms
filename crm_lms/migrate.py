#!/usr/bin/env python
import os
import sys
import django

# Устанавливаем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Инициализируем Django
django.setup()

from django.core.management import execute_from_command_line

# Применяем миграции
execute_from_command_line(['manage.py', 'migrate', 'mentors'])
