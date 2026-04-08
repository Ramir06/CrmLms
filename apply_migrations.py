#!/usr/bin/env python
"""Применение миграций"""
import os
import sys
import subprocess

# Добавляем путь к crm_lms в PYTHONPATH
sys.path.insert(0, r"c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms")

# Устанавливаем правильную рабочую директорию
os.chdir(r"c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms")

# Проверяем что manage.py существует
if os.path.exists("../manage.py"):
    print("manage.py найден, применяем миграции...")
    
    # Применяем миграции для attendance
    print("Применяем миграции для attendance...")
    result = subprocess.run([sys.executable, "../manage.py", "migrate", "attendance"], 
                         capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Миграции для attendance применены успешно")
    else:
        print(f"❌ Ошибка при применении миграций attendance: {result.stderr}")
    
    # Применяем миграции для mentors
    print("Применяем миграции для mentors...")
    result = subprocess.run([sys.executable, "../manage.py", "migrate", "mentors"], 
                         capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Миграции для mentors применены успешно")
    else:
        print(f"❌ Ошибка при применении миграций mentors: {result.stderr}")
    
    print("Все миграции применены!")
else:
    print("manage.py не найден!")
    print("Текущая директория:", os.getcwd())
