from django.core.management.base import BaseCommand
from apps.finance.models import FinanceTransaction, FinanceCategory, FinanceAccount
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = 'Добавляет тестовый филиал'

    def handle(self, *args, **options):
        """Добавляет тестовый филиал"""
        self.stdout.write("=== Добавление тестового филиала ===")
        
        # Получаем все организации
        organizations = Organization.objects.all()
        self.stdout.write(f"Найдено организаций: {organizations.count()}")
        
        for org in organizations:
            self.stdout.write(f"- {org.name}")
            
            # Получаем или создаем категорию и счет
            category, _ = FinanceCategory.objects.get_or_create(
                name='Оплата курсов',
                type='income',
                organization=org,
                defaults={'color': '#10b981'}
            )
            
            account, _ = FinanceAccount.objects.get_or_create(
                name='Основной счёт',
                organization=org,
                defaults={'balance': 0}
            )
            
            # Проверяем, есть ли уже транзакция для этой организации
            existing = FinanceTransaction.objects.filter(
                organization=org,
                branch=org.name
            ).exists()
            
            if not existing:
                # Создаем тестовую транзакцию
                transaction = FinanceTransaction.objects.create(
                    type='income',
                    category=category,
                    amount=8000.00,
                    account=account,
                    description=f'Тестовая транзакция для {org.name}',
                    transaction_date='2024-01-25',
                    organization=org,
                    branch=org.name
                )
                
                self.stdout.write(f"✅ Создана транзакция: {transaction.id} - {transaction.branch}")
            else:
                self.stdout.write(f"ℹ️ Транзакция для {org.name} уже существует")
        
        # Показываем все филиалы
        self.stdout.write("\nВсе филиалы в базе:")
        branches = list(FinanceTransaction.objects.filter(
            branch__isnull=False
        ).exclude(branch='').values_list('branch', flat=True).order_by('branch').distinct())
        
        for branch in branches:
            self.stdout.write(f"- {branch}")
        
        self.stdout.write("\n✅ Работа завершена!")
