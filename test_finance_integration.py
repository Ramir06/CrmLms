#!/usr/bin/env python
"""
Скрипт для тестирования интеграции финансовой системы
"""
import os
import sys
import django

# Устанавливаем путь к Django проекту
project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm_lms')
sys.path.insert(0, project_path)

# Устанавливаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Инициализируем Django
django.setup()

from apps.accounts.models import CustomUser
from apps.courses.models import Course
from apps.students.models import Student
from apps.payments.models import Payment
from apps.salaries.models import SalaryAccrual
from apps.finance.models import FinanceTransaction, FinanceCategory, FinanceAccount
from apps.organizations.models import Organization, OrganizationMember

def test_finance_integration():
    """Тестирует автоматическое создание финансовых транзакций"""
    print("=== Тестирование интеграции финансовой системы ===\n")
    
    # 1. Проверяем наличие организаций
    organizations = Organization.objects.all()
    print(f"1. Найдено организаций: {organizations.count()}")
    for org in organizations:
        print(f"   - {org.name}")
    
    if not organizations.exists():
        print("❌ Нет организаций для теста!")
        return
    
    org = organizations.first()
    
    # 2. Проверяем наличие студентов
    students = Student.objects.all()
    print(f"\n2. Найдено студентов: {students.count()}")
    
    if not students.exists():
        print("❌ Нет студентов для теста!")
        return
    
    student = students.first()
    print(f"   - Тестовый студент: {student.full_name}")
    
    # 3. Проверяем наличие курсов
    courses = Course.objects.all()
    print(f"\n3. Найдено курсов: {courses.count()}")
    
    if not courses.exists():
        print("❌ Нет курсов для теста!")
        return
    
    course = courses.first()
    print(f"   - Тестовый курс: {course.title}")
    
    # 4. Проверяем наличие менторов
    mentors = CustomUser.objects.filter(role='mentor')
    print(f"\n4. Найдено менторов: {mentors.count()}")
    
    if not mentors.exists():
        print("❌ Нет менторов для теста!")
        return
    
    mentor = mentors.first()
    print(f"   - Тестовый ментор: {mentor.get_display_name()}")
    
    # 5. Создаем тестовый платеж
    print(f"\n5. Создание тестового платежа...")
    existing_payments = Payment.objects.filter(student=student, course=course).count()
    print(f"   - Существующих платежей для этой пары: {existing_payments}")
    
    # Создаем платеж
    payment = Payment.objects.create(
        student=student,
        course=course,
        amount=10000.00,
        paid_at='2024-01-15',
        comment='Тестовый платеж для проверки интеграции'
    )
    print(f"   ✅ Создан платеж ID: {payment.id}")
    
    # Проверяем, создалась ли транзакция
    transaction = FinanceTransaction.objects.filter(
        related_entity_type='payment',
        related_entity_id=payment.id
    ).first()
    
    if transaction:
        print(f"   ✅ Автоматически создана транзакция ID: {transaction.id}")
        print(f"   - Тип: {transaction.get_type_display()}")
        print(f"   - Сумма: {transaction.amount}")
        print(f"   - Описание: {transaction.description}")
        print(f"   - Авто-генерация: {transaction.auto_generated}")
    else:
        print("   ❌ Транзакция не создана!")
    
    # 6. Создаем тестовое начисление зарплаты
    print(f"\n6. Создание тестового начисления зарплаты...")
    
    salary = SalaryAccrual.objects.create(
        mentor=mentor,
        course=course,
        month='2024-01-01',
        amount=15000.00,
        paid_status='paid',
        comment='Тестовая зарплата для проверки интеграции'
    )
    print(f"   ✅ Создано начисление зарплаты ID: {salary.id}")
    
    # Проверяем, создалась ли транзакция
    salary_transaction = FinanceTransaction.objects.filter(
        related_entity_type='salary_accrual',
        related_entity_id=salary.id
    ).first()
    
    if salary_transaction:
        print(f"   ✅ Автоматически создана транзакция ID: {salary_transaction.id}")
        print(f"   - Тип: {salary_transaction.get_type_display()}")
        print(f"   - Сумма: {salary_transaction.amount}")
        print(f"   - Описание: {salary_transaction.description}")
        print(f"   - Авто-генерация: {salary_transaction.auto_generated}")
    else:
        print("   ❌ Транзакция не создана!")
    
    # 7. Общая статистика
    print(f"\n7. Общая статистика по транзакциям:")
    all_transactions = FinanceTransaction.objects.all()
    auto_transactions = FinanceTransaction.objects.filter(auto_generated=True)
    manual_transactions = FinanceTransaction.objects.filter(auto_generated=False)
    
    print(f"   - Всего транзакций: {all_transactions.count()}")
    print(f"   - Автоматических: {auto_transactions.count()}")
    print(f"   - Ручных: {manual_transactions.count()}")
    
    # 8. Статистика по категориям
    print(f"\n8. Категории транзакций:")
    categories = FinanceCategory.objects.all()
    for category in categories:
        count = FinanceTransaction.objects.filter(category=category).count()
        print(f"   - {category.name}: {count} транзакций")
    
    # 9. Статистика по счетам
    print(f"\n9. Счета:")
    accounts = FinanceAccount.objects.all()
    for account in accounts:
        count = FinanceTransaction.objects.filter(account=account).count()
        print(f"   - {account.name}: {count} транзакций")
    
    print(f"\n=== Тест завершен ===")
    print(f"Теперь вы можете проверить бухгалтерию по адресу: /admin/finance/")
    print(f"Платеж и зарплата должны отображаться как автоматические транзакции.")

if __name__ == '__main__':
    test_finance_integration()
