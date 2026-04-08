import os
import sys
import django

# Устанавливаем путь к Django проекту
sys.path.append(r'c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Инициализируем Django
django.setup()

from apps.courses.models import Course

def check_course_status():
    """Проверяем статус курса"""
    try:
        course = Course.objects.get(id=53)
        print(f"Курс: {course.title}")
        print(f"ID: {course.id}")
        print(f"Статус: {course.status}")
        print(f"Бесконечный: {course.is_unlimited}")
        print(f"Студентов: {course.course_students.count()}")
        
        # Делаем курс бесконечным если нужно
        if not course.is_unlimited:
            print("\nДелаем курс бесконечным...")
            course.is_unlimited = True
            course.save()
            print(f"Курс теперь бесконечный: {course.is_unlimited}")
        else:
            print("\nКурс уже является бесконечным")
            
    except Course.DoesNotExist:
        print("Курс с ID 53 не найден")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    check_course_status()
