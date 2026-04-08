from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from apps.courses.models import CourseStudent, Course
from apps.attendance.models import AttendanceRecord
from apps.debts.models import Debt
from apps.courses.tickets import TicketBalance
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Создает долги типа "Занятие" для студентов с перерасходом талонов на бесконечных курсах'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course-id',
            type=int,
            help='ID конкретного курса для проверки (опционально)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет создано, но не создавать долги'
        )

    def handle(self, *args, **options):
        course_id = options.get('course_id')
        dry_run = options.get('dry_run', False)
        
        self.stdout.write('=== Обновление долгов по занятиям ===')
        if dry_run:
            self.stdout.write('DRY RUN MODE - долги не будут созданы')
        
        # Получаем бесконечные курсы
        courses = Course.objects.filter(is_unlimited=True)
        if course_id:
            courses = courses.filter(id=course_id)
        
        total_debts_created = 0
        
        for course in courses:
            self.stdout.write(f'\nПроверка курса: {course.title} (ID: {course.id})')
            
            debts_created = self._process_course(course, dry_run)
            total_debts_created += debts_created
            
            if debts_created > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Создано долгов: {debts_created}'
                    )
                )
            else:
                self.stdout.write('  Новых долгов не найдено')
        
        self.stdout.write(self.style.SUCCESS(
            f'\nГотово! Всего создано долгов: {total_debts_created}'
        ))

    def _process_course(self, course, dry_run=False):
        """Обрабатывает один курс"""
        debts_created = 0
        
        # Получаем всех активных студентов
        enrollments = CourseStudent.objects.filter(
            course=course,
            status='active'
        ).select_related('student', 'course').prefetch_related('ticket_balance')
        
        for enrollment in enrollments:
            try:
                ticket_balance = enrollment.ticket_balance
                if ticket_balance is None:
                    continue
                
                remaining_tickets = int(ticket_balance.remaining_tickets or 0)
                total_tickets = int(ticket_balance.total_tickets or 0)
                used_tickets = int(ticket_balance.used_tickets or 0)
                
                # Проверяем перерасход: использовано больше чем куплено, или остаток отрицательный
                has_overdue = (used_tickets > total_tickets) or (remaining_tickets < 0)
                
                if has_overdue:
                    # У студента перерасход, проверяем посещения
                    attendance_records = AttendanceRecord.objects.filter(
                        lesson__course=course,
                        student=enrollment.student,
                        attendance_status='present'
                    ).order_by('lesson__lesson_date')
                    
                    # Считаем посещения сверх талонов
                    total_tickets = int(ticket_balance.total_tickets or 0)
                    overdue_visits = max(0, len(attendance_records) - total_tickets)
                    
                    if overdue_visits > 0:
                        self.stdout.write(
                            f'  Студент: {enrollment.student.full_name} - '
                            f'всего талонов: {total_tickets}, '
                            f'использовано: {used_tickets}, '
                            f'остаток: {remaining_tickets}, '
                            f'просроченных посещений: {overdue_visits}'
                        )
                        
                        if not dry_run:
                            created_count = self._create_lesson_debts_for_student(
                                enrollment, attendance_records, total_tickets
                            )
                            debts_created += created_count
                        else:
                            debts_created += overdue_visits
                            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  Ошибка при обработке студента {enrollment.student.full_name}: {str(e)}'
                    )
                )
                continue
        
        return debts_created

    def _create_lesson_debts_for_student(self, enrollment, attendance_records, total_tickets):
        """Создает долги для конкретного студента"""
        from django.utils import timezone
        
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        # Определяем цену за занятие
        course = enrollment.course
        if course.duration_months and course.duration_months > 0:
            lesson_price = course.price / course.duration_months
        else:
            lesson_price = course.price / 3
        
        lesson_price = max(lesson_price, 1)
        
        debts_created = 0
        paid_visits = 0
        
        for record in attendance_records:
            if paid_visits < total_tickets:
                paid_visits += 1
            else:
                # Это посещение сверх талонов, создаем долг
                try:
                    # Проверяем, есть ли уже долг за этот месяц
                    existing_debt = Debt.objects.filter(
                        student=enrollment.student,
                        course=course,
                        debt_type='lesson',
                        month=current_month,
                        year=current_year,
                        status='active'
                    ).first()
                    
                    if existing_debt:
                        # Увеличиваем существующий долг
                        existing_debt.total_amount += lesson_price
                        existing_debt.note += f"\n+ Урок {record.lesson_id} ({timezone.now().strftime('%d.%m.%Y')})"
                        existing_debt.save()
                    else:
                        # Создаем новый долг
                        debt = Debt.objects.create(
                            student=enrollment.student,
                            course=course,
                            total_amount=lesson_price,
                            paid_amount=0,
                            status='active',
                            debt_type='lesson',
                            month=current_month,
                            year=current_year,
                            note=f'Долг за посещение занятия без талонов. Урок {record.lesson_id} ({timezone.now().strftime("%d.%m.%Y")})'
                        )
                    
                    debts_created += 1
                    
                except Exception as e:
                    logger.error(f"Error creating debt for lesson {record.lesson_id}: {str(e)}")
                    continue
        
        return debts_created
