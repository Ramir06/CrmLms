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
            'view_calendar': True,
            'access_admin_panel': True
        }
    )
    print(f'✅ Роль "{accountant_role.name}" создана с {len(accountant_role.permissions)} разрешениями:')
    for perm, enabled in accountant_role.permissions.items():
        if enabled:
            print(f'  - {perm}')
except Exception as e:
    print(f'⚠️ Ошибка: {e}')

# Создаем роль 'Оператор' (только расписание)
try:
    operator_role = Role.objects.create(
        name='Оператор',
        description='Роль с доступом только к расписанию',
        permissions={
            'view_calendar': True,
            'view_settings': True
        }
    )
    print(f'✅ Роль "{operator_role.name}" создана с {len(operator_role.permissions)} разрешениями:')
    for perm, enabled in operator_role.permissions.items():
        if enabled:
            print(f'  - {perm}')
except Exception as e:
    print(f'⚠️ Ошибка: {e}')

print('\n🎉 Роли успешно созданы! Теперь можно:')
print('1. Создать пользователя с ролью "Бухгалтер"')
print('2. Создать пользователя с ролью "Оператор"')
print('3. Проверить, что меню скрывает недоступные разделы')
