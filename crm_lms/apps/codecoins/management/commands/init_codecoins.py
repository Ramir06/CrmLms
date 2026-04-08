from django.core.management.base import BaseCommand
from django.db import transaction
from apps.codecoins.models import CoinScale, CoinWithdrawalSetting
from decimal import Decimal


class Command(BaseCommand):
    help = 'Initialize codecoins system with default scales and settings'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing Codecoins system...')
        
        with transaction.atomic():
            # Создаем настройки вывода
            setting, created = CoinWithdrawalSetting.objects.get_or_create(
                id=1,
                defaults={
                    'is_open': False,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('✓ Created withdrawal settings'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Withdrawal settings already exist'))
            
            # Создаем шкалы по умолчанию
            default_scales = [
                {'title': 'Отличная активность', 'value': Decimal('5'), 'sort_order': 1},
                {'title': 'Хорошая активность', 'value': Decimal('3'), 'sort_order': 2},
                {'title': 'Пассивность', 'value': Decimal('-2'), 'sort_order': 3},
                {'title': 'Отсутствие', 'value': Decimal('-5'), 'sort_order': 4},
                {'title': 'Помощь одногруппникам', 'value': Decimal('3'), 'sort_order': 5},
                {'title': 'Выполнение ДЗ', 'value': Decimal('2'), 'sort_order': 6},
                {'title': 'Не выполнил ДЗ', 'value': Decimal('-3'), 'sort_order': 7},
                {'title': 'Опоздание', 'value': Decimal('-1'), 'sort_order': 8},
                {'title': 'Kahoot победитель', 'value': Decimal('5'), 'sort_order': 9},
                {'title': 'Kahoot участие', 'value': Decimal('2'), 'sort_order': 10},
                {'title': 'Typing рекорд', 'value': Decimal('3'), 'sort_order': 11},
                {'title': 'Проектная работа', 'value': Decimal('10'), 'sort_order': 12},
            ]
            
            created_count = 0
            updated_count = 0
            
            for scale_data in default_scales:
                scale, created = CoinScale.objects.get_or_create(
                    title=scale_data['title'],
                    defaults={
                        'value': scale_data['value'],
                        'sort_order': scale_data['sort_order'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created scale: {scale.title}')
                    )
                else:
                    # Обновляем существующую шкалу
                    scale.value = scale_data['value']
                    scale.sort_order = scale_data['sort_order']
                    scale.is_active = True
                    scale.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Updated scale: {scale.title}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Codecoins system initialized successfully!'
                f'\n   - Scales created: {created_count}'
                f'\n   - Scales updated: {updated_count}'
                f'\n   - Total scales: {CoinScale.objects.count()}'
            )
        )
