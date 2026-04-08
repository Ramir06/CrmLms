from django.core.management.base import BaseCommand
from django.db import transaction
from apps.finance.models import FinanceTransaction, FinanceCategory, FinanceAccount
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = 'Присваивает организацию существующим финансовым данным на основе создателя'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем присвоение организаций финансовым данным...')
        
        # Получаем все организации
        organizations = list(Organization.objects.all())
        
        if not organizations:
            self.stdout.write(self.style.WARNING('Организации не найдены'))
            return
        
        # Обновляем транзакции
        transactions_updated = 0
        transactions = FinanceTransaction.objects.filter(organization__isnull=True)
        
        for tx in transactions:
            # Пробуем определить организацию по создателю
            if tx.created_by and hasattr(tx.created_by, 'organizations'):
                user_orgs = tx.created_by.organizations.all()
                if user_orgs.exists():
                    tx.organization = user_orgs.first()
                    tx.save()
                    transactions_updated += 1
                    self.stdout.write(f'Транзакция {tx.id} -> организация {tx.organization.name}')
        
        # Обновляем категории
        categories_updated = 0
        categories = FinanceCategory.objects.filter(organization__isnull=True)
        
        # Создаем общие категории для каждой организации
        default_categories = [
            {'name': 'Зарплата менторам', 'type': 'expense', 'color': '#ef4444'},
            {'name': 'Аренда офиса', 'type': 'expense', 'color': '#f59e0b'},
            {'name': 'Оплата обучения', 'type': 'income', 'color': '#10b981'},
            {'name': 'Материалы', 'type': 'expense', 'color': '#8b5cf6'},
            {'name': 'Маркетинг', 'type': 'expense', 'color': '#ec4899'},
            {'name': 'Коммунальные услуги', 'type': 'expense', 'color': '#6366f1'},
        ]
        
        for org in organizations:
            for cat_data in default_categories:
                # Проверяем, существует ли такая категория для организации
                existing = FinanceCategory.objects.filter(
                    organization=org,
                    name=cat_data['name'],
                    type=cat_data['type']
                ).exists()
                
                if not existing:
                    category = FinanceCategory.objects.create(
                        organization=org,
                        **cat_data
                    )
                    categories_updated += 1
                    self.stdout.write(f'Создана категория {category.name} для {org.name}')
        
        # Обновляем счета
        accounts_updated = 0
        accounts = FinanceAccount.objects.filter(organization__isnull=True)
        
        for org in organizations:
            # Создаем базовые счета для организации
            default_accounts = [
                {'name': 'Наличные', 'balance': 0, 'description': 'Наличные деньги'},
                {'name': 'Банковский счет', 'balance': 0, 'description': 'Основной банковский счет'},
                {'name': 'Касса', 'balance': 0, 'description': 'Операционная касса'},
            ]
            
            for acc_data in default_accounts:
                existing = FinanceAccount.objects.filter(
                    organization=org,
                    name=acc_data['name']
                ).exists()
                
                if not existing:
                    account = FinanceAccount.objects.create(
                        organization=org,
                        **acc_data
                    )
                    accounts_updated += 1
                    self.stdout.write(f'Создан счет {account.name} для {org.name}')
        
        # Выводим статистику
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Обновление завершено:'))
        self.stdout.write(f'Транзакций обновлено: {transactions_updated}')
        self.stdout.write(f'Категорий создано: {categories_updated}')
        self.stdout.write(f'Счетов создано: {accounts_updated}')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        # Показываем остатки без организации
        remaining_transactions = FinanceTransaction.objects.filter(organization__isnull=True).count()
        remaining_categories = FinanceCategory.objects.filter(organization__isnull=True).count()
        remaining_accounts = FinanceAccount.objects.filter(organization__isnull=True).count()
        
        if remaining_transactions > 0 or remaining_categories > 0 or remaining_accounts > 0:
            self.stdout.write(self.style.WARNING('Осталось без организации:'))
            self.stdout.write(f'Транзакций: {remaining_transactions}')
            self.stdout.write(f'Категорий: {remaining_categories}')
            self.stdout.write(f'Счетов: {remaining_accounts}')
        else:
            self.stdout.write(self.style.SUCCESS('Все данные успешно привязаны к организациям!'))
