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
from apps.lessons.models import Lesson
from apps.courses.models import Course, CourseStudent
from apps.attendance.models import AttendanceRecord
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== Анализ проблемы с посещаемостью у ментора ===")
print()

# 1. Проверяем пользователей
print("1. Проверка пользователей:")
mentors = User.objects.filter(role='mentor')
for mentor in mentors:
    print(f"  Ментор: {mentor.username} - Роль: {mentor.role}")
print()

# 2. Проверяем курсы и их менторов
print("2. Проверка курсов:")
courses = Course.objects.all()[:5]
for course in courses:
    print(f"  Курс: {course.title} - Ментор: {course.mentor.username if course.mentor else 'None'}")
print()

# 3. Проверяем уроки
print("3. Проверка уроков:")
lessons = Lesson.objects.all()[:5]
for lesson in lessons:
    print(f"  Урок {lesson.id}: {lesson.title} - Курс: {lesson.course.title} - Ментор: {lesson.course.mentor.username if lesson.course.mentor else 'None'}")
print()

# 4. Проверяем записи посещаемости
print("4. Проверка записей посещаемости:")
attendance_records = AttendanceRecord.objects.all()[:5]
for record in attendance_records:
    print(f"  Запись: Студент {record.student.full_name} - Урок {record.lesson.title} - Статус: {record.attendance_status} - Кто отметил: {record.marked_by.username if record.marked_by else 'None'}")
print()

# 5. Проверяем права доступа для конкретного ментора
if mentors.exists():
    test_mentor = mentors.first()
    print(f"5. Проверка прав доступа для ментора {test_mentor.username}:")
    
    for lesson in lessons:
        from apps.core.mixins_substitute import can_mark_attendance
        can_mark = can_mark_attendance(test_mentor, lesson.id)
        print(f"  Урок {lesson.id}: Может отмечать = {can_mark}")
        if not can_mark:
            print(f"    Причина: не является основным ментором или заменяющим")
print()

# 6. Проверяем активных студентов на курсах
print("6. Проверка активных студентов:")
for course in courses:
    active_students = CourseStudent.objects.filter(course=course, status='active').count()
    print(f"  Курс {course.title}: {active_students} активных студентов")
print()

print("=== Анализ завершен ===")
