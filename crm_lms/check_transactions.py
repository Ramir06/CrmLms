import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.finance.models import FinanceTransaction
from apps.organizations.models import Organization

print("🔍 Проверка транзакций...")
print("=" * 50)

# Проверяем последние транзакции
transactions = FinanceTransaction.objects.all().order_by('-created_at')[:5]
print('Последние 5 транзакций:')
for tx in transactions:
    org_name = tx.organization.name if tx.organization else 'Без организации'
    print(f'ID: {tx.id}, Тип: {tx.type}, Сумма: {tx.amount}, Организация: {org_name}, Описание: "{tx.description}"')

print("\n" + "=" * 50)
print('Все организации:')
for org in Organization.objects.all():
    print(f'ID: {org.id}, Название: {org.name}')

print("\n" + "=" * 50)
print('Проверяем фильтрацию по организациям:')
for org in Organization.objects.all():
    org_txs = FinanceTransaction.objects.filter(organization=org)
    print(f'{org.name}: {org_txs.count()} транзакций')
