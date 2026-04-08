#!/usr/bin/env python
"""
Тест для проверки функциональности отображения оплаченных месяцев
"""
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'crm_lms'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.students.models import Student
from apps.courses.models import CourseStudent
from apps.payments.models import Payment

def test_payment_months():
    print("=== Тестирование функциональности оплаченных месяцев ===\n")
    
    # Берем студента с оплатами
    student = Student.objects.get(id=13)  # RAMIR PROGRAMMER
    print(f"Студент: {student.full_name}")
    
    # Получаем активные курсы студента
    active_courses = CourseStudent.objects.filter(
        student=student, 
        status='active'
    ).select_related('course')
    
    print(f"\nАктивные курсы ({active_courses.count()}):")
    for cs in active_courses:
        print(f"  - {cs.course.title} (длительность: {cs.course.duration_months} мес.)")
        
        # Получаем оплаты для этого курса
        payments = Payment.objects.filter(
            student=student,
            course=cs.course
        )
        
        # Собираем все оплаченные месяцы
        all_paid_months = []
        for payment in payments:
            if payment.months_paid:
                if isinstance(payment.months_paid, list):
                    all_paid_months.extend([int(m) for m in payment.months_paid if m is not None])
                elif isinstance(payment.months_paid, int):
                    all_paid_months.append(payment.months_paid)
        
        # Удаляем дубликаты, сохраняя порядок
        seen = set()
        unique_paid_months = []
        for month in all_paid_months:
            if month not in seen:
                seen.add(month)
                unique_paid_months.append(month)
        
        print(f"    Оплаченные месяцы: {unique_paid_months}")
        
        # Показываем доступные месяцы для оплаты
        available_months = []
        for i in range(1, cs.course.duration_months + 1):
            if i not in unique_paid_months:
                available_months.append(i)
        
        print(f"    Доступные для оплаты: {available_months}")
        print()
    
    print("=== Проверка завершена ===")

if __name__ == '__main__':
    test_payment_months()
