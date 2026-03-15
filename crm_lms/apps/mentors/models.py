from django.db import models
from apps.core.models import TimeStampedModel
import random
import string


class MentorProfile(TimeStampedModel):
    SALARY_TYPE_CHOICES = [
        ('fixed', 'Фиксированная'),
        ('hourly', 'Почасовая'),
        ('percent', 'Процент'),
        ('mixed', 'Смешанная'),
    ]

    user = models.OneToOneField(
        'accounts.CustomUser', on_delete=models.CASCADE,
        related_name='mentor_profile', verbose_name='Пользователь'
    )
    short_name = models.CharField(max_length=100, blank=True, verbose_name='Короткое имя')
    specialization = models.CharField(max_length=200, blank=True, verbose_name='Специализация')
    bio = models.TextField(blank=True, verbose_name='О себе')
    salary_type = models.CharField(
        max_length=10, choices=SALARY_TYPE_CHOICES, default='fixed', verbose_name='Тип зарплаты'
    )
    fixed_salary = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name='Фиксированная зарплата'
    )
    # hourly_rate будет добавлено после миграции
    # hourly_rate = models.DecimalField(
    #     max_digits=8, decimal_places=2, default=0, verbose_name='Ставка за час'
    # )
    percent_salary = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='Процент от оплат'
    )
    hired_at = models.DateField(null=True, blank=True, verbose_name='Дата найма')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    # Поля 2FA будут добавлены после миграции
    # two_factor_enabled = models.BooleanField(default=False, verbose_name='Двухфакторная аутентификация')
    # two_factor_code = models.CharField(max_length=6, blank=True, verbose_name='Код 2FA')
    # two_factor_code_expires = models.DateTimeField(null=True, blank=True, verbose_name='Срок действия кода')

    class Meta:
        verbose_name = 'Профиль ментора'
        verbose_name_plural = 'Профили менторов'

    def __str__(self):
        return self.user.get_display_name()

    def get_display_name(self):
        return self.short_name or self.user.get_display_name()

    def generate_2fa_code(self):
        """Генерирует 6-значный код для 2FA (временно не работает до миграций)"""
        # Временно возвращаем заглушку
        code = ''.join(random.choices(string.digits, k=6))
        print(f"2FA код для {self.user.email}: {code} (временно не сохраняется)")
        return code

    def verify_2fa_code(self, code):
        """Проверяет 2FA код (временно не работает до миграций)"""
        # Временно всегда возвращаем False
        print(f"Проверка 2FA кода {code} для {self.user.email} (временно не работает)")
        return False

    def send_2fa_code(self):
        """Отправляет 2FA код на email (временно не работает до миграций)"""
        code = self.generate_2fa_code()
        
        # Здесь нужно добавить реальную отправку email
        # from django.core.mail import send_mail
        # send_mail(
        #     'Код подтверждения',
        #     f'Ваш код подтверждения: {code}',
        #     'noreply@example.com',
        #     [self.user.email],
        #     fail_silently=False,
        # )
        
        return code

    def calculate_monthly_salary(self, year, month):
        """Рассчитывает зарплату за месяц на основе типа оплаты"""
        from django.utils import timezone
        from datetime import date
        from apps.courses.models import Course
        from apps.lessons.models import Lesson
        
        if self.salary_type == 'fixed':
            return self.fixed_salary
        
        elif self.salary_type == 'hourly':
            # Получаем количество рабочих часов за месяц
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            # Получаем уроки ментора за этот период
            lessons = Lesson.objects.filter(
                course__mentor=self.user,
                lesson_date__gte=start_date,
                lesson_date__lt=end_date,
                status='completed'
            )
            
            # Считаем рабочие часы (по времени урока)
            total_hours = 0
            for lesson in lessons:
                if lesson.start_time and lesson.end_time:
                    # Разница между началом и концом урока
                    start = lesson.start_time
                    end = lesson.end_time
                    duration = (end.hour - start.hour) + (end.minute - start.minute) / 60
                    total_hours += max(duration, 0)  # Убедимся что не отрицательное
            
            # Временно используем значение по умолчанию до миграции
            hourly_rate = getattr(self, 'hourly_rate', 500)  # Значение по умолчанию 500
            return total_hours * hourly_rate
        
        elif self.salary_type == 'percent':
            # Получаем общие оплаты за курсы ментора за месяц
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            from apps.payments.models import Payment
            total_payments = Payment.objects.filter(
                course__mentor=self.user,
                paid_at__gte=start_date,
                paid_at__lt=end_date
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            return total_payments * (self.percent_salary / 100)
        
        elif self.salary_type == 'mixed':
            # Смешанная: фиксированная + проценты
            base_salary = self.fixed_salary
            
            # Добавляем проценты
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            from apps.payments.models import Payment
            total_payments = Payment.objects.filter(
                course__mentor=self.user,
                paid_at__gte=start_date,
                paid_at__lt=end_date
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            percent_amount = total_payments * (self.percent_salary / 100)
            return base_salary + percent_amount
        
        return 0

    def get_salary_breakdown(self, year, month):
        """Возвращает детализацию зарплаты за месяц"""
        from datetime import date
        from apps.lessons.models import Lesson
        from apps.payments.models import Payment
        
        # Временно используем значение по умолчанию до миграции
        hourly_rate = getattr(self, 'hourly_rate', 500)  # Значение по умолчанию 500
        
        breakdown = {
            'type': self.salary_type,
            'base_amount': 0,
            'hours_worked': 0,
            'hourly_rate': hourly_rate,
            'total_payments': 0,
            'percent_rate': self.percent_salary,
            'percent_amount': 0,
            'total': 0
        }
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        if self.salary_type == 'fixed':
            breakdown['base_amount'] = self.fixed_salary
            breakdown['total'] = self.fixed_salary
            
        elif self.salary_type == 'hourly':
            lessons = Lesson.objects.filter(
                course__mentor=self.user,
                lesson_date__gte=start_date,
                lesson_date__lt=end_date,
                status='completed'
            )
            
            total_hours = 0
            for lesson in lessons:
                if lesson.start_time and lesson.end_time:
                    start = lesson.start_time
                    end = lesson.end_time
                    duration = (end.hour - start.hour) + (end.minute - start.minute) / 60
                    total_hours += max(duration, 0)
            
            # Временно используем значение по умолчанию до миграции
            hourly_rate = getattr(self, 'hourly_rate', 500)  # Значение по умолчанию 500
            breakdown['hours_worked'] = total_hours
            breakdown['total'] = total_hours * hourly_rate
            
        elif self.salary_type in ['percent', 'mixed']:
            total_payments = Payment.objects.filter(
                course__mentor=self.user,
                paid_at__gte=start_date,
                paid_at__lt=end_date
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            breakdown['total_payments'] = total_payments
            breakdown['percent_amount'] = total_payments * (self.percent_salary / 100)
            
            if self.salary_type == 'mixed':
                breakdown['base_amount'] = self.fixed_salary
                breakdown['total'] = self.fixed_salary + breakdown['percent_amount']
            else:
                breakdown['total'] = breakdown['percent_amount']
        
        return breakdown
