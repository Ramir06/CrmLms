#!/usr/bin/env python
import os
import sys
import django

# Устанавливаем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Role

# Создаем роль 'Бухгалтер'
try:
    accountant_role = Role.objects.create(
        name='Бухгалтер',
        description='Роль для управления финансовыми операциями',
        permissions={
            'view_payments': True,
            'add_payments': True,
            'edit_payments': True,
            'view_reports': True,
            'view_students': True,
            'access_admin_panel': True
        }
    )
    print(f'Роль "{accountant_role.name}" создана с {len(accountant_role.permissions)} разрешениями')
except Exception as e:
    print(f'Ошибка: {e}')

# Создаем роль 'Менеджер'
try:
    manager_role = Role.objects.create(
        name='Менеджер',
        description='Роль для управления персоналом и студентами',
        permissions={
            'view_students': True,
            'add_students': True,
            'edit_students': True,
            'view_mentors': True,
            'add_mentors': True,
            'edit_mentors': True,
            'view_courses': True,
            'view_payments': True,
            'view_reports': True,
            'access_admin_panel': True
        }
    )
    print(f'Роль "{manager_role.name}" создана с {len(manager_role.permissions)} разрешениями')
except Exception as e:
    print(f'Ошибка: {e}')
