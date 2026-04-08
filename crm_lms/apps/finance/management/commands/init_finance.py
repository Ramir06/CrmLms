from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.finance.signals import create_initial_categories_and_accounts


class Command(BaseCommand):
    help = 'Инициализирует бухгалтерию для существующих организаций'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Получаем все организации
        organizations = Organization.objects.all()
        
        if not organizations.exists():
            self.stdout.write(self.style.WARNING('Организации не найдены. Сначала создайте организации.'))
            return
        
        created_count = 0
        
        for organization in organizations:
            try:
                # Создаем начальные категории и счета
                create_initial_categories_and_accounts(organization)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Бухгалтерия инициализирована для организации: {organization.name}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка при инициализации бухгалтерии для {organization.name}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Бухгалтерия успешно инициализирована для {created_count} организаций')
        )
