#!/usr/bin/env python
import os
import sys

# Устанавливаем правильную рабочую директорию
os.chdir(r"c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms")

# Добавляем текущую директорию в Python path
sys.path.insert(0, os.getcwd())

# Устанавливаем переменные окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Импортируем и настраиваем Django
import django
django.setup()

# Теперь можно импортировать модели Django
from apps.courses.models import Course, CourseStudent
from apps.courses.tickets import TicketAttendance, TicketBalance
from apps.attendance.models import AttendanceRecord
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== Проверка данных по талонам и посещаемости ===")
print()

# 1. Проверяем курсы
print("1. Проверка курсов:")
courses = Course.objects.all()
for course in courses:
    print(f"  Курс: {course.title} - Бесконечный: {course.is_unlimited}")
print()

# 2. Проверяем студентов на бесконечных курсах
print("2. Проверка студентов на бесконечных курсах:")
for course in courses:
    if course.is_unlimited:
        enrollments = CourseStudent.objects.filter(course=course, status='active')
        print(f"  Курс {course.title}:")
        for enrollment in enrollments:
            print(f"    Студент: {enrollment.student.full_name}")
            
            # Проверяем баланс талонов
            try:
                balance = enrollment.ticket_balance
                print(f"      Баланс талонов: {balance.remaining_tickets}/{balance.total_tickets}")
            except:
                print(f"      Баланс талонов: НЕ НАЙДЕН")
            
            # Проверяем посещения по талонам
            attendances = enrollment.ticket_attendances.all()
            print(f"      Посещений по талонам: {attendances.count()}")
            for att in attendances:
                print(f"        - {att.lesson_date} ({att.lessons_count} занятий)")
            
            # Проверяем обычную посещаемость
            regular_attendances = AttendanceRecord.objects.filter(
                student=enrollment.student,
                lesson__course=course
            )
            print(f"      Обычных посещений: {regular_attendances.count()}")
            for att in regular_attendances:
                print(f"        - {att.lesson.lesson_date}: {att.attendance_status}")
        print()

print("=== Проверка завершена ===")
