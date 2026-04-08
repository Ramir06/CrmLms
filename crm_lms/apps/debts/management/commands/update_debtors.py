from django.core.management.base import BaseCommand
from apps.debts.models import Debt


class Command(BaseCommand):
    help = 'Обновляет список должников на основе бизнес-логики'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Обновление списка должников...')
            
            # Используем новый менеджер для определения должников
            debtors = Debt.objects.get_debtors()
            created_count = Debt.objects.create_or_update_debts()
            
            self.stdout.write(
                self.style.SUCCESS(f'Найдено должников: {len(debtors)}')
            )
            
            for enrollment in debtors:
                self.stdout.write(f'  - {enrollment.student.full_name} ({enrollment.course.title})')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при обновлении должников: {str(e)}')
            )

    
