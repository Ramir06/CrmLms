#!/usr/bin/env python
"""
Тестирование системы разрешений
"""
import os
import sys
import django

# Устанавливаем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    
    from apps.accounts.models import CustomUser, Role
    
    print("🔍 Проверка системы разрешений...")
    
    # Проверяем, что модель Role работает
    roles_count = Role.objects.count()
    print(f"✅ Модель Role: {roles_count} ролей в базе данных")
    
    # Проверяем, что CustomUser имеет метод has_permission
    try:
        user = CustomUser.objects.first()
        if user:
            test_perm = user.has_permission('view_calendar')
            print(f"✅ Метод has_permission работает: {test_perm}")
        else:
            print("⚠️ Пользователи не найдены в базе данных")
    except Exception as e:
        print(f"❌ Ошибка в методе has_permission: {e}")
    
    print("\n🎯 Система готова к тестированию!")
    print("📝 Инструкция:")
    print("1. Зайдите в админ-панель: http://127.0.0.1:8000/admin/")
    print("2. Создайте роль с нужными разрешениями")
    print("3. Создайте пользователя с этой ролью")
    print("4. Проверьте динамическое меню")
    
except Exception as e:
    print(f"❌ Ошибка инициализации Django: {e}")
    print("Убедитесь, что сервер запущен: python manage.py runserver")
