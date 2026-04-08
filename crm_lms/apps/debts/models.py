from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from apps.core.models import TimeStampedModel


class DebtManager(models.Manager):
    def get_debtors(self):
        """Получить всех должников на основе бизнес-логики"""
        today = timezone.now().date()
        debtors = []
        
        # Получаем всех активных студентов на курсах
        from apps.courses.models import CourseStudent
        active_enrollments = CourseStudent.objects.filter(
            status='active'
        ).select_related('student', 'course')
        
        for enrollment in active_enrollments:
            if self._is_student_debtor(enrollment, today):
                debtors.append(enrollment)
        
        return debtors
    
    def _is_student_debtor(self, enrollment, today):
        """Check if student is a debtor"""
        student = enrollment.student
        course = enrollment.course
        
        # Get paid months with years
        paid_months = self._get_paid_months_with_years(student, course)
        
        # Main rule: if current month is not paid, student is a debtor
        if (today.year, today.month) not in paid_months:
            return True
        
        return False
    
    def _months_between(self, start_date, end_date):
        """Вычислить количество полных месяцев между двумя датами"""
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if end_date.day < start_date.day:
            months -= 1
        return max(0, months)
    
    def _get_paid_months_with_years(self, student, course):
        """Get set of paid months with years for student as tuples (year, month)"""
        from apps.payments.models import Payment
        
        payments = Payment.objects.filter(
            student=student,
            course=course,
            amount__gt=0  # Only consider payments with positive amount
        )
        
        paid_months = set()
        for payment in payments:
            if payment.months_paid:
                # If specific months are specified in months_paid
                for month_data in payment.months_paid:
                    if isinstance(month_data, (int, str)):
                        # Convert string month to int
                        month = int(month_data)
                        paid_months.add((payment.paid_at.year, month))
                    elif isinstance(month_data, dict):
                        # If dictionary with month and year
                        month = month_data.get('month')
                        year = month_data.get('year', payment.paid_at.year)
                        if month:
                            month = int(month)
                            paid_months.add((year, month))
                # Always add the payment month as well (as fallback)
                paid_months.add((payment.paid_at.year, payment.paid_at.month))
            else:
                # For old payments without months_paid, add payment month and year
                paid_months.add((payment.paid_at.year, payment.paid_at.month))
        
        return paid_months
    
    def create_or_update_debts(self):
        """Create or update debts for all debtors"""
        debtors = self.get_debtors()
        today = timezone.now()
        
        # Get all current active debts
        current_active_debts = self.filter(status='active')
        
        # Mark as paid debts for students who are no longer debtors
        for debt in current_active_debts:
            is_currently_debtor = any(
                d.student == debt.student and d.course == debt.course 
                for d in debtors
            )
            if not is_currently_debtor:
                debt.status = 'paid'
                debt.paid_amount = debt.total_amount
                debt.save()
        
        # Create new debts for current debtors
        for enrollment in debtors:
            student = enrollment.student
            course = enrollment.course
            
            # Check if there's already an active debt for current month
            existing_debt = self.filter(
                student=student,
                course=course,
                status='active',
                month=today.month,
                year=today.year
            ).first()
            
            if not existing_debt:
                # Create a new debt
                monthly_price = course.price / max(1, course.duration_months)
                
                self.create(
                    student=student,
                    course=course,
                    total_amount=monthly_price,
                    paid_amount=0,
                    debt_type='monthly',
                    month=today.month,
                    year=today.year,
                    note=f'Automatically identified as debtor for {today.strftime("%B %Y")}'
                )


class Debt(TimeStampedModel):
    STATUS_CHOICES = [
        ('active', 'Активный долг'),
        ('paid', 'Погашен'),
        ('written_off', 'Списан'),
    ]
    
    DEBT_TYPE_CHOICES = [
        ('monthly', 'Месячный'),
        ('lesson', 'Занятие'),
    ]

    objects = DebtManager()

    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='debts', verbose_name='Студент'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='debts', verbose_name='Курс'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Всего к оплате')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Оплачено')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    debt_type = models.CharField(max_length=15, choices=DEBT_TYPE_CHOICES, default='monthly', verbose_name='Тип долга')
    note = models.TextField(blank=True, verbose_name='Примечание')
    
    # Новые поля для отслеживания месяца долга
    month = models.PositiveSmallIntegerField(verbose_name='Месяц', default=1)
    year = models.PositiveSmallIntegerField(verbose_name='Год', default=2024)

    class Meta:
        verbose_name = 'Долг'
        verbose_name_plural = 'Долги'
        ordering = ['-created_at']
        unique_together = ['student', 'course', 'month', 'year']

    def __str__(self):
        return f'{self.student} — долг {self.debt_amount} за {self.month}.{self.year}'

    @property
    def debt_amount(self):
        return self.total_amount - self.paid_amount
