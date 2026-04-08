#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== Тестирование сигналов ===")

# Импортируем модели
from apps.payments.models import Payment
from apps.finance.models import FinanceTransaction
from apps.salaries.models import SalaryAccrual
from apps.students.models import Student
from apps.courses.models import Course
from apps.accounts.models import CustomUser

# Проверим наличие данных
students = Student.objects.all()[:1]
courses = Course.objects.all()[:1]
users = CustomUser.objects.filter(role='mentor')[:1]

print(f"Студентов: {students.count()}")
print(f"Курсов: {courses.count()}")
print(f"Менторов: {users.count()}")

if students.exists() and courses.exists():
    student = students.first()
    course = courses.first()
    
    print(f"\n=== Создание тестового платежа ===")
    print(f"Студент: {student.full_name}")
    print(f"Курс: {course.title}")
    print(f"Организация студента: {student.organization}")
    
    # Создаем платеж - это должно вызвать сигнал
    payment = Payment.objects.create(
        student=student,
        course=course,
        amount=5000.00,
        paid_at="2025-03-30",
        comment="Тестовый платеж",
        created_by=users.first() if users.exists() else None
    )
    
    print(f"Платеж создан: {payment.id}")
    
    # Проверяем появилась ли транзакция
    transaction = FinanceTransaction.objects.filter(
        related_entity_type='payment',
        related_entity_id=payment.id
    ).first()
    
    if transaction:
        print(f"✅ Транзакция создана: {transaction.amount} ({transaction.get_type_display()})")
        print(f"   Описание: {transaction.description}")
        print(f"   Организация: {transaction.organization}")
    else:
        print("❌ Транзакция НЕ создана")
        
        # Проверим все транзакции
        all_tx = FinanceTransaction.objects.all()
        print(f"Всего транзакций в системе: {all_tx.count()}")
        for tx in all_tx[:3]:
            print(f"  - {tx.get_type_display()}: {tx.amount} ({tx.description[:30]}...)")

if users.exists():
    mentor = users.first()
    
    print(f"\n=== Создание тестовой зарплаты ===")
    print(f"Ментор: {mentor.get_full_name()}")
    print(f"Организация ментора: {mentor.organization}")
    
    # Создаем зарплату - это должно вызвать сигнал
    salary = SalaryAccrual.objects.create(
        mentor=mentor,
        course=courses.first() if courses.exists() else None,
        amount=30000.00,
        paid_status='paid',  # Выплаченная - должна создать транзакцию
        month="2025-03-01",
        comment="Тестовая зарплата"
    )
    
    print(f"Зарплата создана: {salary.id}")
    
    # Проверяем появилась ли транзакция
    transaction = FinanceTransaction.objects.filter(
        related_entity_type='salary_accrual',
        related_entity_id=salary.id
    ).first()
    
    if transaction:
        print(f"✅ Транзакция создана: {transaction.amount} ({transaction.get_type_display()})")
        print(f"   Описание: {transaction.description}")
        print(f"   Организация: {transaction.organization}")
    else:
        print("❌ Транзакция НЕ создана")

print("\n=== Тест завершен ===")
