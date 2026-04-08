import os
import sys
import django

# Устанавливаем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Инициализируем Django
django.setup()

from apps.courses.models import Course, CourseStudent

def check_course_unlimited():
    """Проверяем статус курса"""
    try:
        # Проверяем курс 53
        course = Course.objects.get(id=53)
        print(f"Курс: {course.title}")
        print(f"ID: {course.id}")
        print(f"Бесконечный: {course.is_unlimited}")
        print(f"Студентов: {course.course_students.count()}")
        
        # Проверяем студентов курса
        students = CourseStudent.objects.filter(course=course)
        print(f"\nСтуденты курса:")
        for student in students:
            print(f"  - {student.student.full_name} (ID: {student.id})")
            print(f"    Баланс талонов: {student.ticket_balance.total_tickets if student.ticket_balance else 'Нет'}")
        
        # Если курс не бесконечный, делаем его бесконечным
        if not course.is_unlimited:
            print(f"\nДелаем курс бесконечным...")
            course.is_unlimited = True
            course.save()
            print(f"Курс теперь бесконечный: {course.is_unlimited}")
        
    except Course.DoesNotExist:
        print("Курс с ID 53 не найден")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    check_course_unlimited()
