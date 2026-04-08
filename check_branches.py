#!/usr/bin/env python
"""
Скрипт для проверки филиалов
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

from apps.finance.models import FinanceTransaction
from apps.organizations.models import Organization

def check_branches():
    """Проверяем филиалы в системе"""
    print("=== Проверка филиалов ===\n")
    
    # Показываем все транзакции с филиалами
    print('Все транзакции с филиалами:')
    for tx in FinanceTransaction.objects.all():
        print(f'ID: {tx.id}, Филиал: {tx.branch}, Организация: {tx.organization.name if tx.organization else "None"}')
    
    print('\nВсе уникальные филиалы:')
    branches = list(FinanceTransaction.objects.filter(
        branch__isnull=False
    ).exclude(branch='').values_list('branch', flat=True).order_by('branch').distinct())
    print(branches)
    
    # Показываем все организации
    print('\nВсе организации:')
    for org in Organization.objects.all():
        print(f'- {org.name}')
        
        # Показываем филиалы для каждой организации
        org_branches = list(FinanceTransaction.objects.filter(
            organization=org,
            branch__isnull=False
        ).exclude(branch='').values_list('branch', flat=True).order_by('branch').distinct())
        print(f'  Филиалы: {org_branches}')

if __name__ == '__main__':
    check_branches()
