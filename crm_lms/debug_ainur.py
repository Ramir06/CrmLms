#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== Проверка зарплаты Айнур Сеткали ===")

from apps.salaries.models import SalaryAccrual
from apps.finance.models import FinanceTransaction
from apps.accounts.models import CustomUser
from apps.organizations.models import Organization

# Ищем пользователя Айнур Сеткали
users = CustomUser.objects.filter(full_name__icontains='Айнур').filter(full_name__icontains='Сеткали')
print(f"Найдено пользователей: {users.count()}")

for user in users:
    print(f"  - {user.full_name} (role: {user.role}, org: {user.organization})")

if users.exists():
    user = users.first()
    
    # Ищем зарплаты за март
    from datetime import date
    march_date = date(2025, 3, 1)
    
    salaries = SalaryAccrual.objects.filter(mentor=user, month=march_date)
    print(f"\nЗарплат за март 2025: {salaries.count()}")
    
    for salary in salaries:
        print(f"  - ID: {salary.id}, сумма: {salary.amount}, статус: {salary.paid_status}")
        
        # Ищем связанную транзакцию
        tx = FinanceTransaction.objects.filter(
            related_entity_type='salary_accrual',
            related_entity_id=salary.id
        ).first()
        
        if tx:
            print(f"    ✅ Транзакция найдена: {tx.amount} ({tx.get_type_display()})")
            print(f"       Организация: {tx.organization}")
            print(f"       Авто: {tx.auto_generated}")
        else:
            print(f"    ❌ Транзакция НЕ найдена")
            
            # Пробуем создать принудительно
            print(f"    Пробуем создать транзакцию...")
            try:
                from apps.finance.signals import create_salary_transaction
                tx = create_salary_transaction(salary)
                if tx:
                    print(f"    ✅ Транзакция создана принудительно: {tx.id}")
                else:
                    print(f"    ❌ Не удалось создать транзакцию")
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")

# Проверяем организацию Рамир
org = Organization.objects.filter(name__icontains='Рамир').first()
if org:
    print(f"\nОрганизация Рамир: {org.name}")
    
    # Проверяем категории и счета
    from apps.finance.models import FinanceCategory, FinanceAccount
    
    categories = FinanceCategory.objects.filter(organization=org)
    accounts = FinanceAccount.objects.filter(organization=org)
    
    print(f"  Категорий: {categories.count()}")
    for cat in categories:
        print(f"    - {cat.name} ({cat.type})")
    
    print(f"  Счетов: {accounts.count()}")
    for acc in accounts:
        print(f"    - {acc.name}")
        
    # Все транзакции организации
    all_tx = FinanceTransaction.objects.filter(organization=org)
    print(f"  Всех транзакций: {all_tx.count()}")
    for tx in all_tx[:5]:
        print(f"    - {tx.get_type_display()}: {tx.amount} - {tx.description[:50]}...")

print("\n=== Проверка завершена ===")
