from django.core.management.base import BaseCommand
from apps.organizations.models import Organization
from apps.finance.models import FinanceCategory, FinanceAccount, FinanceTransaction
from apps.finance.signals import create_initial_categories_and_accounts


class Command(BaseCommand):
    help = 'Исправляет финансовые данные для мультиорганизационной системы'

    def handle(self, *args, **options):
        self.stdout.write('Начинаю исправление финансовых данных...')
        
        # 1. Создаем категории и счета для всех организаций
        organizations = Organization.objects.all()
        self.stdout.write(f'Найдено организаций: {organizations.count()}')
        
        for org in organizations:
            self.stdout.write(f'Обрабатываю организацию: {org.name}')
            create_initial_categories_and_accounts(org)
        
        # 2. Исправляем транзакции без организации
        transactions_without_org = FinanceTransaction.objects.filter(organization__isnull=True)
        self.stdout.write(f'Транзакций без организации: {transactions_without_org.count()}')
        
        if transactions_without_org.exists():
            # Берем первую организацию как организацию по умолчанию
            default_org = organizations.first()
            if default_org:
                updated_count = transactions_without_org.update(organization=default_org)
                self.stdout.write(f'Обновлено транзакций: {updated_count}')
        
        # 3. Исправляем категории без организации
        categories_without_org = FinanceCategory.objects.filter(organization__isnull=True)
        self.stdout.write(f'Категорий без организации: {categories_without_org.count()}')
        
        if categories_without_org.exists():
            default_org = organizations.first()
            if default_org:
                # Удаляем дубликаты категорий
                category_names = categories_without_org.values_list('name', 'type').distinct()
                
                for name, cat_type in category_names:
                    # Находим или создаем категорию для организации
                    category, created = FinanceCategory.objects.get_or_create(
                        name=name,
                        type=cat_type,
                        organization=default_org,
                        defaults={'color': '#6366f1'}
                    )
                    
                    # Переносим транзакции
                    FinanceTransaction.objects.filter(
                        category__in=categories_without_org.filter(name=name, type=cat_type)
                    ).update(category=category)
                
                # Удаляем старые категории без организации
                deleted_count = categories_without_org.delete()[0]
                self.stdout.write(f'Удалено категорий без организации: {deleted_count}')
        
        # 4. Исправляем счета без организации
        accounts_without_org = FinanceAccount.objects.filter(organization__isnull=True)
        self.stdout.write(f'Счетов без организации: {accounts_without_org.count()}')
        
        if accounts_without_org.exists():
            default_org = organizations.first()
            if default_org:
                # Удаляем дубликаты счетов
                account_names = accounts_without_org.values_list('name', flat=True).distinct()
                
                for name in account_names:
                    # Находим или создаем счет для организации
                    account, created = FinanceAccount.objects.get_or_create(
                        name=name,
                        organization=default_org,
                        defaults={'balance': 0, 'description': f'Счет {name}'}
                    )
                    
                    # Переносим транзакции
                    FinanceTransaction.objects.filter(
                        account__in=accounts_without_org.filter(name=name)
                    ).update(account=account)
                
                # Удаляем старые счета без организации
                deleted_count = accounts_without_org.delete()[0]
                self.stdout.write(f'Удалено счетов без организации: {deleted_count}')
        
        self.stdout.write(self.style.SUCCESS('Исправление завершено!'))
