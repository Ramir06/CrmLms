import os
import sys
import subprocess

# Устанавливаем правильную рабочую директорию
os.chdir(r"c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms")

# Проверяем что manage.py существует
if os.path.exists("manage.py"):
    print("manage.py найден, запускаем Django сервер...")
    # Запускаем Django
    subprocess.run([sys.executable, "manage.py", "runserver"])
else:
    print("manage.py не найден!")
    print("Текущая директория:", os.getcwd())
    print("Файлы в директории:")
    for file in os.listdir("."):
        print(f"  {file}")
