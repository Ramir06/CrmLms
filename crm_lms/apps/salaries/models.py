from django.db import models
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from apps.core.models import TimeStampedModel


class SalaryAccrual(TimeStampedModel):
    PAID_STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('paid', 'Выплачено'),
        ('cancelled', 'Отменено'),
    ]

    mentor = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.CASCADE,
        related_name='salary_accruals', verbose_name='Ментор',
        limit_choices_to={'role': 'mentor'}
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='salary_accruals', verbose_name='Курс'
    )
    month = models.DateField(verbose_name='Месяц')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    paid_status = models.CharField(
        max_length=15, choices=PAID_STATUS_CHOICES, default='pending', verbose_name='Статус выплаты'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    class Meta:
        verbose_name = 'Начисление зарплаты'
        verbose_name_plural = 'Начисления зарплат'
        ordering = ['-month']

    def __str__(self):
        return f'{self.mentor} — {self.month.strftime("%B %Y")} — {self.amount}'
    
    @classmethod
    def calculate_monthly_salary(cls, mentor, year, month):
        """Автоматический расчет зарплаты ментора за месяц"""
        from apps.lessons.models import Lesson
        from apps.courses.models import Course
        
        # Получаем первый и последний день месяца
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        total_amount = 0
        
        # Получаем все курсы ментора
        mentor_courses = Course.objects.filter(
            Q(mentor=mentor) | Q(assistant_mentor=mentor)
        ).distinct()
        
        for course in mentor_courses:
            if course.salary_type == 'hourly':
                # Почасовая оплата
                course_amount = cls._calculate_hourly_salary(course, mentor, first_day, last_day)
            elif course.salary_type == 'monthly':
                # Фиксированная месячная оплата - сумма остается такой же
                course_amount = course.price
            elif course.salary_type == 'percentage':
                # Процент от оплат
                course_amount = cls._calculate_percentage_salary(course, mentor, first_day, last_day)
            elif course.salary_type == 'course':
                # Оплата за курс (пропорционально количеству проведенных уроков)
                course_amount = cls._calculate_course_salary(course, mentor, first_day, last_day)
            else:
                course_amount = 0
            
            total_amount += course_amount
        
        return total_amount
    
    @classmethod
    def _calculate_hourly_salary(cls, course, mentor, first_day, last_day):
        """Расчет почасовой зарплаты"""
        from apps.lessons.models import Lesson
        
        # Получаем все уроки курса за месяц
        lessons = Lesson.objects.filter(
            course=course,
            lesson_date__gte=first_day,
            lesson_date__lte=last_day,
            status='completed'  # Только проведенные уроки
        )
        
        total_hours = 0
        
        for lesson in lessons:
            # Определяем, кто проводил урок
            if lesson.temporary_mentor:
                # Если была замена, час засчитывается заменяющему
                if lesson.temporary_mentor == mentor:
                    # Урок проводил текущий ментор как замена
                    total_hours += lesson.duration_minutes / 60
                # Если замена был другой ментор, текущий ментор не получает за этот час
            else:
                # Если замены не было, час засчитывается основному ментору
                if course.mentor == mentor or course.assistant_mentor == mentor:
                    total_hours += lesson.duration_minutes / 60
        
        return total_hours * course.hourly_rate
    
    @classmethod
    def _calculate_percentage_salary(cls, course, mentor, first_day, last_day):
        """Расчет зарплаты как процента от оплат"""
        from apps.payments.models import Payment
        
        # Получаем все оплаты за курс в указанном месяце
        payments = Payment.objects.filter(
            course=course,
            payment_date__gte=first_day,
            payment_date__lte=last_day,
            status='paid'
        )
        
        total_payments = sum(payment.amount for payment in payments)
        
        # Рассчитываем процент от общей суммы оплат
        return total_payments * (course.salary_percentage / 100)
    
    @classmethod
    def _calculate_course_salary(cls, course, mentor, first_day, last_day):
        """Расчет зарплаты за курс (пропорционально проведенным урокам)"""
        from apps.lessons.models import Lesson
        
        # Получаем общее количество уроков в курсе
        total_lessons = Lesson.objects.filter(course=course).count()
        if total_lessons == 0:
            return 0
        
        # Получаем проведенные уроки за месяц
        completed_lessons = Lesson.objects.filter(
            course=course,
            lesson_date__gte=first_day,
            lesson_date__lte=last_day,
            status='completed'
        )
        
        mentor_completed_lessons = 0
        for lesson in completed_lessons:
            if lesson.temporary_mentor:
                if lesson.temporary_mentor == mentor:
                    mentor_completed_lessons += 1
            else:
                if course.mentor == mentor or course.assistant_mentor == mentor:
                    mentor_completed_lessons += 1
        
        # Пропорциональный расчет
        if mentor_completed_lessons > 0:
            return (course.price / total_lessons) * mentor_completed_lessons
        return 0
    
    @classmethod
    def auto_generate_accruals(cls, year, month):
        """Генерация начислений зарплаты для всех менторов за месяц"""
        from apps.accounts.models import CustomUser
        
        mentors = CustomUser.objects.filter(role='mentor')
        
        for mentor in mentors:
            amount = cls.calculate_monthly_salary(mentor, year, month)
            
            # Проверяем, существует ли уже начисление за этот месяц
            existing = cls.objects.filter(
                mentor=mentor,
                month=datetime(year, month, 1).date()
            ).first()
            
            if existing:
                # Обновляем существующее начисление
                existing.amount = amount
                existing.save()
            else:
                # Создаем новое начисление
                cls.objects.create(
                    mentor=mentor,
                    month=datetime(year, month, 1).date(),
                    amount=amount,
                    comment='Автоматически рассчитано'
                )
    
    def get_salary_details(self):
        """Получить детальную информацию о расчете зарплаты"""
        from apps.lessons.models import Lesson
        from apps.courses.models import Course
        
        first_day = (self.month.replace(day=1))
        if self.month.month == 12:
            last_day = datetime(self.month.year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(self.month.year, self.month.month + 1, 1).date() - timedelta(days=1)
        
        details = {
            'courses': [],
            'total_hours': 0,
            'total_lessons': 0,
            'substituted_lessons': 0,
            'cancelled_lessons': 0
        }
        
        mentor_courses = Course.objects.filter(
            Q(mentor=self.mentor) | Q(assistant_mentor=self.mentor)
        ).distinct()
        
        for course in mentor_courses:
            course_details = {
                'course': course,
                'amount': 0,
                'hours': 0,
                'lessons': [],
                'salary_type': course.salary_type
            }
            
            lessons = Lesson.objects.filter(
                course=course,
                lesson_date__gte=first_day,
                lesson_date__lte=last_day
            )
            
            for lesson in lessons:
                lesson_info = {
                    'date': lesson.lesson_date,
                    'time': f"{lesson.start_time} - {lesson.end_time}",
                    'duration': lesson.duration_minutes / 60,
                    'status': lesson.status,
                    'mentor': lesson.current_mentor,
                    'is_substituted': lesson.is_substituted,
                    'earned_by_mentor': False
                }
                
                if lesson.status == 'completed':
                    if lesson.temporary_mentor:
                        if lesson.temporary_mentor == self.mentor:
                            lesson_info['earned_by_mentor'] = True
                            course_details['hours'] += lesson.duration_minutes / 60
                            details['substituted_lessons'] += 1
                    else:
                        if course.mentor == self.mentor or course.assistant_mentor == self.mentor:
                            lesson_info['earned_by_mentor'] = True
                            course_details['hours'] += lesson.duration_minutes / 60
                elif lesson.status == 'cancelled':
                    details['cancelled_lessons'] += 1
                
                course_details['lessons'].append(lesson_info)
            
            # Расчет суммы для курса
            if course.salary_type == 'hourly':
                course_details['amount'] = course_details['hours'] * course.hourly_rate
            elif course.salary_type == 'monthly':
                # Фиксированная месячная оплата - сумма остается такой же
                course_details['amount'] = course.price
            elif course.salary_type == 'percentage':
                # Рассчитываем процент от оплат за месяц
                from apps.payments.models import Payment
                payments = Payment.objects.filter(
                    course=course,
                    payment_date__gte=first_day,
                    payment_date__lte=last_day,
                    status='paid'
                )
                total_payments = sum(payment.amount for payment in payments)
                course_details['amount'] = total_payments * (course.salary_percentage / 100)
            elif course.salary_type == 'course':
                total_course_lessons = Lesson.objects.filter(course=course).count()
                if total_course_lessons > 0:
                    mentor_lessons = sum(1 for lesson in course_details['lessons'] if lesson['earned_by_mentor'])
                    course_details['amount'] = (course.price / total_course_lessons) * mentor_lessons
            
            details['courses'].append(course_details)
            details['total_hours'] += course_details['hours']
            details['total_lessons'] += len([l for l in course_details['lessons'] if l['earned_by_mentor']])
        
        return details
