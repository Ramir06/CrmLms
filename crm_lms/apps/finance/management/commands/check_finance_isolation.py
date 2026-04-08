from django.core.management.base import BaseCommand
from django.db.models import Sum
from apps.finance.models import FinanceTransaction, FinanceAccount, FinanceCategory
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = 'Проверяет изоляцию данных в бухгалтерии'

    def handle(self, *args, **options):
        print("🔍 Проверка изоляции данных в бухгалтерии...\n")
        
        # Получаем все организации
        organizations = Organization.objects.all()
        print(f"📊 Найдено организаций: {organizations.count()}")
        
        for org in organizations:
            print(f"\n🏢 Организация: {org.name}")
            
            # Проверяем транзакции
            transactions = FinanceTransaction.objects.filter(organization=org)
            accounts = FinanceAccount.objects.filter(organization=org)
            categories = FinanceCategory.objects.filter(organization=org)
            
            print(f"  💰 Транзакции: {transactions.count()}")
            print(f"  🏦 Счета: {accounts.count()}")
            print(f"  📁 Категории: {categories.count()}")
            
            # Проверяем есть ли транзакции без организации
            orphan_transactions = FinanceTransaction.objects.filter(organization__isnull=True)
            if orphan_transactions.exists():
                print(f"  ⚠️  Транзакций без организации: {orphan_transactions.count()}")
                for tx in orphan_transactions[:3]:
                    print(f"    - ID: {tx.id}, Сумма: {tx.amount}, Описание: {tx.description}")
            
            # Проверяем есть ли счета без организации
            orphan_accounts = FinanceAccount.objects.filter(organization__isnull=True)
            if orphan_accounts.exists():
                print(f"  ⚠️  Счетов без организации: {orphan_accounts.count()}")
                for acc in orphan_accounts[:3]:
                    print(f"    - ID: {acc.id}, Название: {acc.name}")
            
            # Проверяем есть ли категории без организации
            orphan_categories = FinanceCategory.objects.filter(organization__isnull=True)
            if orphan_categories.exists():
                print(f"  ⚠️  Категорий без организации: {orphan_categories.count()}")
                for cat in orphan_categories[:3]:
                    print(f"    - ID: {cat.id}, Название: {cat.name}")
        
        # Проверяем транзакции, которые видят все организации
        print(f"\n🚨 Проверка транзакций, видимых всем организациям:")
        shared_transactions = FinanceTransaction.objects.filter(organization__isnull=True)
        if shared_transactions.exists():
            print(f"  ❌ Найдено {shared_transactions.count()} транзакций без организации!")
            print("  Это критическая проблема безопасности!")
        else:
            print("  ✅ Все транзакции привязаны к организациям")
        
        print(f"\n✅ Проверка завершена!")
