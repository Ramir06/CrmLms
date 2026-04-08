#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== Проверка последних транзакций ===")

from apps.finance.models import FinanceTransaction
from apps.salaries.models import SalaryAccrual
from apps.organizations.models import Organization

# 1. Проверяем все последние транзакции
print("\n1. Последние 10 транзакций в системе:")
recent_tx = FinanceTransaction.objects.all().order_by('-created')[:10]
for tx in recent_tx:
    print(f"  ID: {tx.id} - {tx.get_type_display()}: {tx.amount}")
    print(f"    Орг: {tx.organization}")
    print(f"    Описание: {tx.description[:50]}...")
    print(f"    Авто: {tx.auto_generated}")
    print(f"    Связь: {tx.related_entity_type} - {tx.related_entity_id}")
    print()

# 2. Проверяем транзакции по организациям
print("2. Транзакции по организациям:")
orgs = Organization.objects.all()
for org in orgs:
    tx_count = FinanceTransaction.objects.filter(organization=org).count()
    print(f"  {org.name}: {tx_count} транзакций")

# 3. Проверяем зарплаты и их транзакции
print("\n3. Последние зарплаты и их транзакции:")
recent_salaries = SalaryAccrual.objects.all().order_by('-created')[:5]
for salary in recent_salaries:
    print(f"  Зарплата {salary.id}: {salary.mentor.get_display_name()} - {salary.amount} ({salary.paid_status})")
    
    # Ищем связанную транзакцию
    tx = FinanceTransaction.objects.filter(
        related_entity_type='salary_accrual',
        related_entity_id=salary.id
    ).first()
    
    if tx:
        print(f"    ✅ Транзакция {tx.id}: {tx.amount} в орг {tx.organization}")
    else:
        print(f"    ❌ Транзакция не найдена")

# 4. Проверяем автоматические транзакции
print("\n4. Автоматические транзакции:")
auto_tx = FinanceTransaction.objects.filter(auto_generated=True)
print(f"Всего авто-транзакций: {auto_tx.count()}")
for tx in auto_tx[:5]:
    print(f"  {tx.get_type_display()}: {tx.amount} - {tx.description[:40]}...")

print("\n=== Проверка завершена ===")
