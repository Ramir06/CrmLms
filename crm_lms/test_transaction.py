import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.finance.models import FinanceTransaction, FinanceCategory, FinanceAccount
from apps.organizations.models import Organization

print("🧪 Тест создания транзакции...")
print("=" * 50)

# Получаем организации
orgs = Organization.objects.all()
print(f'Всего организаций: {orgs.count()}')

for org in orgs:
    print(f'\n🏢 Организация: {org.name} (ID: {org.id})')
    
    # Проверяем категории
    categories = FinanceCategory.objects.filter(organization=org)
    print(f'  📁 Категорий: {categories.count()}')
    
    # Проверяем счета
    accounts = FinanceAccount.objects.filter(organization=org)
    print(f'  🏦 Счетов: {accounts.count()}')
    
    # Проверяем транзакции
    transactions = FinanceTransaction.objects.filter(organization=org)
    print(f'  💰 Транзакций: {transactions.count()}')
    
    if transactions.exists():
        print('  Последние транзакции:')
        for tx in transactions.order_by('-created_at')[:3]:
            print(f'    - ID: {tx.id}, Тип: {tx.type}, Сумма: {tx.amount}, Описание: "{tx.description}"')

print("\n" + "=" * 50)
print("✅ Тест завершен!")
