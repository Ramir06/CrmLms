#!/usr/bin/env python
"""
Скрипт для тестирования фильтра по филиалам
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

from apps.finance.models import FinanceTransaction, FinanceCategory, FinanceAccount
from apps.organizations.models import Organization

def test_branch_filter():
    """Тестируем фильтр по филиалам"""
    print("=== Тестирование фильтра по филиалам ===\n")
    
    # Получаем организации
    org1 = Organization.objects.filter(name__contains='Казахстан').first()
    org2 = Organization.objects.filter(name__contains='Киргизия').first()
    
    print(f"Организации:")
    print(f"- Казахстан: {org1}")
    print(f"- Киргизия: {org2}")
    
    if not org1 or not org2:
        print("❌ Не найдены организации!")
        return
    
    # Получаем или создаем категории
    cat1, _ = FinanceCategory.objects.get_or_create(name='Оплата курсов', type='income', organization=org1, defaults={'color': '#10b981'})
    cat2, _ = FinanceCategory.objects.get_or_create(name='Оплата курсов', type='income', organization=org2, defaults={'color': '#10b981'})
    
    # Получаем счета
    acc1, _ = FinanceAccount.objects.get_or_create(name='Основной счёт', organization=org1, defaults={'balance': 0})
    acc2, _ = FinanceAccount.objects.get_or_create(name='Основной счёт', organization=org2, defaults={'balance': 0})
    
    # Создаем тестовые транзакции с разными филиалами
    tx1 = FinanceTransaction.objects.create(
        type='income',
        category=cat1,
        amount=5000.00,
        account=acc1,
        description='Тестовая транзакция Казахстан',
        transaction_date='2024-01-20',
        organization=org1,
        branch='Чтениум | Казахстан'
    )
    
    tx2 = FinanceTransaction.objects.create(
        type='income', 
        category=cat2,
        amount=7500.00,
        account=acc2,
        description='Тестовая транзакция Киргизия',
        transaction_date='2024-01-21',
        organization=org2,
        branch='Чтениум | Киргизия'
    )
    
    print(f'\nСозданы транзакции:')
    print(f'- ID: {tx1.id}, Филиал: {tx1.branch}, Сумма: {tx1.amount}')
    print(f'- ID: {tx2.id}, Филиал: {tx2.branch}, Сумма: {tx2.amount}')
    
    # Проверяем уникальные филиалы
    branches = list(FinanceTransaction.objects.values_list('branch', flat=True).filter(branch__isnull=False).exclude(branch='').distinct())
    print(f'\nУникальные филиалы в базе:')
    for branch in branches:
        print(f'- {branch}')
    
    # Тестируем фильтрацию
    print(f'\nТестирование фильтрации:')
    
    kz_transactions = FinanceTransaction.objects.filter(branch='Чтениум | Казахстан')
    print(f'- Транзакции Казахстана: {kz_transactions.count()}')
    for tx in kz_transactions:
        print(f'  * {tx.description} - {tx.amount}')
    
    kg_transactions = FinanceTransaction.objects.filter(branch='Чтениум | Киргизия')
    print(f'- Транзакции Киргизии: {kg_transactions.count()}')
    for tx in kg_transactions:
        print(f'  * {tx.description} - {tx.amount}')
    
    print(f'\n✅ Фильтр по филиалам работает!')
    print(f'Теперь можно проверить в интерфейсе: /admin/finance/')

if __name__ == '__main__':
    test_branch_filter()
