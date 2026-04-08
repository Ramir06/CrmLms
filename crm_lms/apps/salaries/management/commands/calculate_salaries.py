from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from apps.salaries.models import SalaryAccrual


class Command(BaseCommand):
    help = 'Автоматический расчет зарплат менторов за указанный месяц'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=datetime.now().year,
            help='Год для расчета зарплаты (по умолчанию: текущий год)'
        )
        parser.add_argument(
            '--month',
            type=int,
            default=datetime.now().month,
            help='Месяц для расчета зарплаты (по умолчанию: текущий месяц)'
        )
        parser.add_argument(
            '--all-mentors',
            action='store_true',
            help='Рассчитать для всех менторов'
        )
        parser.add_argument(
            '--mentor-id',
            type=int,
            help='ID ментора для расчета (требуется если не указан --all-mentors)'
        )

    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        
        if options['all_mentors']:
            self.stdout.write(f'Расчет зарплат для всех менторов за {month:02d}/{year}...')
            
            try:
                SalaryAccrual.auto_generate_accruals(year, month)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Зарплаты успешно рассчитаны за {month:02d}/{year}')
                )
                
                # Показываем статистику
                accruals = SalaryAccrual.objects.filter(
                    month=datetime(year, month, 1).date()
                )
                
                total_amount = sum(accrual.amount for accrual in accruals)
                self.stdout.write(f'📊 Статистика:')
                self.stdout.write(f'   • Всего менторов: {accruals.count()}')
                self.stdout.write(f'   • Общая сумма: {total_amount:,.2f} ₽')
                
                for accrual in accruals:
                    details = accrual.get_salary_details()
                    self.stdout.write(
                        f'   • {accrual.mentor.get_full_name()}: '
                        f'{accrual.amount:,.2f} ₽ '
                        f'({details["total_hours"]:.1f}ч, {details["total_lessons"]} уроков)'
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка при расчете зарплат: {str(e)}')
                )
                
        elif options['mentor_id']:
            try:
                from apps.accounts.models import CustomUser
                mentor = CustomUser.objects.get(id=options['mentor_id'], role='mentor')
                
                self.stdout.write(f'Расчет зарплаты для ментора {mentor.get_full_name()} за {month:02d}/{year}...')
                
                amount = SalaryAccrual.calculate_monthly_salary(mentor, year, month)
                
                # Создаем или обновляем начисление
                existing = SalaryAccrual.objects.filter(
                    mentor=mentor,
                    month=datetime(year, month, 1).date()
                ).first()
                
                if existing:
                    existing.amount = amount
                    existing.save()
                    self.stdout.write(f'✅ Обновлено существующее начисление: {amount:,.2f} ₽')
                else:
                    SalaryAccrual.objects.create(
                        mentor=mentor,
                        month=datetime(year, month, 1).date(),
                        amount=amount,
                        comment='Автоматически рассчитано'
                    )
                    self.stdout.write(f'✅ Создано новое начисление: {amount:,.2f} ₽')
                
                # Показываем детали
                if existing:
                    details = existing.get_salary_details()
                    self.stdout.write(f'📊 Детали расчета:')
                    self.stdout.write(f'   • Всего часов: {details["total_hours"]:.1f}')
                    self.stdout.write(f'   • Проведено уроков: {details["total_lessons"]}')
                    self.stdout.write(f'   • Уроков с заменой: {details["substituted_lessons"]}')
                    self.stdout.write(f'   • Отменено уроков: {details["cancelled_lessons"]}')
                    
                    for course_detail in details['courses']:
                        self.stdout.write(
                            f'   • {course_detail["course"].title}: '
                            f'{course_detail["amount"]:,.2f} ₽ '
                            f'({course_detail["hours"]:.1f}ч, тип: {course_detail["salary_type"]})'
                        )
                
            except CustomUser.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ментор с ID {options["mentor_id"]} не найден')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка при расчете зарплаты: {str(e)}')
                )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Укажите либо --all-mentors, либо --mentor-id')
            )
