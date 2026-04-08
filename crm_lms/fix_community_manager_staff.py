#!/usr/bin/env python
"""
Исправление is_staff для Community Manager
"""
import os
import sys
import django

# Устанавливаем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    
    from apps.accounts.models import CustomUser
    
    print("🔧 Исправление is_staff для пользователей с кастомными ролями...")
    
    # Находим всех пользователей с кастомными ролями
    users_with_custom_roles = CustomUser.objects.filter(custom_role__isnull=False)
    
    updated_count = 0
    for user in users_with_custom_roles:
        if not user.is_staff:
            user.is_staff = True
            user.save()
            print(f"✅ Обновлен пользователь: {user.username} ({user.get_role_display()}) - is_staff=True")
            updated_count += 1
        else:
            print(f"ℹ️ Пользователь {user.username} уже имеет is_staff=True")
    
    # Также проверяем стандартные роли admin и superadmin
    admin_users = CustomUser.objects.filter(role__in=['admin', 'superadmin'])
    for user in admin_users:
        if not user.is_staff:
            user.is_staff = True
            user.save()
            print(f"✅ Обновлен администратор: {user.username} ({user.get_role_display()}) - is_staff=True")
            updated_count += 1
    
    print(f"\n🎉 Готово! Обновлено {updated_count} пользователей")
    print("📋 Теперь Community Manager имеет доступ к Django admin!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    print("Убедитесь, что сервер запущен: python manage.py runserver")
