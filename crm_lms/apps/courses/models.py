from django.db import models
from django.db.models import Sum
from django.conf import settings
from apps.core.models import TimeStampedModel, OrganizationMixin


class Course(OrganizationMixin, TimeStampedModel):
    STATUS_CHOICES = [
        ('planned', 'Запланирован'),
        ('active', 'Активный'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]
    FORMAT_CHOICES = [
        ('offline', 'Оффлайн'),
        ('online', 'Онлайн'),
        ('hybrid', 'Гибрид'),
    ]
    DAY_CHOICES = [
        ('mon_wed_fri', 'Пн/Ср/Пт'),
        ('tue_thu_sat', 'Вт/Чт/Сб'),
        ('mon_to_fri', 'Пн-Пт'),
        ('sat_sun', 'Сб/Вс'),
        ('custom', 'Другое'),
    ]

    title = models.CharField(max_length=200, default='Новый курс', verbose_name='Название')
    slug = models.SlugField(max_length=200, blank=True, default='', verbose_name='Slug')
    subject = models.CharField(max_length=100, blank=True, verbose_name='Предмет/Направление')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', verbose_name='Статус')
    mentor = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mentor_courses', verbose_name='Ментор',
        limit_choices_to={'role': 'mentor'}
    )
    assistant_mentor = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assistant_courses', verbose_name='Помощник ментора',
        limit_choices_to={'role': 'mentor'}
    )
    start_date = models.DateField(null=True, blank=True, verbose_name='Дата начала')
    end_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')
    duration_months = models.PositiveSmallIntegerField(default=3, verbose_name='Длительность (мес.)')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Стоимость')
    room = models.CharField(max_length=100, blank=True, verbose_name='Кабинет')
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='offline', verbose_name='Формат')
    days_of_week = models.JSONField(default=list, verbose_name='Дни недели')
    lesson_start_time = models.TimeField(null=True, blank=True, verbose_name='Время начала')
    lesson_end_time = models.TimeField(null=True, blank=True, verbose_name='Время окончания')
    capacity = models.PositiveSmallIntegerField(default=15, verbose_name='Вместимость')
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        verbose_name='Почасовая ставка ментора',
        help_text='Ставка за час работы для почасовой оплаты'
    )
    salary_type = models.CharField(
        max_length=10, 
        choices=[
            ('hourly', 'Почасовая'),
            ('monthly', 'Фиксированная'),
            ('percentage', 'Процент от оплат'),
            ('course', 'За курс')
        ],
        default='monthly', 
        verbose_name='Тип оплаты'
    )
    salary_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name='Процент от оплат',
        help_text='Процент от суммы оплат студентов за курс'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    is_unlimited = models.BooleanField(default=False, verbose_name='Бесконечный курс')
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')
    color = models.CharField(max_length=7, default='#7c3aed', verbose_name='Цвет (HEX)')
    online_lesson_link = models.URLField(max_length=500, blank=True, verbose_name='Ссылка на онлайн урок')
    chat_link = models.URLField(max_length=500, blank=True, verbose_name='Ссылка на чат')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            self.slug = slugify(self.title) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    @property
    def is_effectively_unlimited(self):
        """Возвращает True если курс бесконечный или у организации включена оплата по занятиям"""
        return self.is_unlimited or (self.organization and self.organization.payment_per_lesson)

    @property
    def current_students_count(self):
        return self.course_students.filter(status='active').count()

    @property
    def fill_display(self):
        return f'{self.current_students_count}/{self.capacity}'

    def get_days_display_short(self):
        """Отображение дней недели в кратком виде"""
        if not self.days_of_week:
            return 'Не указано'
        
        day_names = {
            'mon': 'Пн', 'tue': 'Вт', 'wed': 'Ср', 'thu': 'Чт',
            'fri': 'Пт', 'sat': 'Сб', 'sun': 'Вс'
        }
        
        days = [day_names[day] for day in self.days_of_week if day in day_names]
        return ', '.join(days) if days else 'Не указано'

    def generate_lessons(self, start_date=None, end_date=None):
        """Генерирует уроки для курса на основе дней недели"""
        from apps.lessons.models import Lesson
        from datetime import datetime, timedelta
        
        if not start_date:
            start_date = self.start_date
        if not end_date:
            end_date = self.end_date
            
        if not start_date or not end_date or not self.days_of_week:
            return []
        
        # Маппинг дней недели на числа Python (0=Пн, 6=Вс)
        day_map = {
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
            'fri': 4, 'sat': 5, 'sun': 6
        }
        
        target_days = [day_map[day] for day in self.days_of_week if day in day_map]
        lessons = []
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in target_days:
                lesson = Lesson.objects.create(
                    course=self,
                    lesson_date=current_date,
                    start_time=self.lesson_start_time or datetime.strptime('09:00', '%H:%M').time(),
                    end_time=self.lesson_end_time or datetime.strptime('10:30', '%H:%M').time(),
                    room=self.room,
                    created_by=self.mentor
                )
                lessons.append(lesson)
            current_date += timedelta(days=1)
            
        return lessons

    # Методы для работы с несколькими менторами
    def get_main_mentors(self):
        """Получить основных менторов курса"""
        return self.course_mentors.filter(role='main', is_active=True).select_related('mentor')
    
    def get_assistant_mentors(self):
        """Получить помощников менторов курса"""
        return self.course_mentors.filter(role='assistant', is_active=True).select_related('mentor')
    
    def get_guest_mentors(self):
        """Получить гостевых менторов курса"""
        return self.course_mentors.filter(role='guest', is_active=True).select_related('mentor')
    
    def get_all_mentors(self):
        """Получить всех менторов курса"""
        return self.course_mentors.filter(is_active=True).select_related('mentor').order_by('role', 'mentor__first_name')
    
    def add_mentor(self, mentor, role='main'):
        """Добавить ментора к курсу"""
        CourseMentor.objects.get_or_create(
            course=self,
            mentor=mentor,
            defaults={'role': role}
        )
    
    def remove_mentor(self, mentor):
        """Удалить ментора с курса"""
        CourseMentor.objects.filter(course=self, mentor=mentor).delete()
    
    @property
    def mentors_list(self):
        """Получить список всех менторов для отображения"""
        return [cm.mentor for cm in self.get_all_mentors()]
    
    @property
    def main_mentor(self):
        """Получить первого основного ментора для обратной совместимости"""
        main_mentors = self.get_main_mentors()
        return main_mentors.first().mentor if main_mentors.exists() else self.mentor


class CourseStudent(TimeStampedModel):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('left', 'Выбыл'),
        ('frozen', 'Заморожен'),
        ('graduated', 'Окончил'),
        ('expelled', 'Отчислен')
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_students', verbose_name='Курс')
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='course_enrollments', verbose_name='Студент'
    )
    joined_at = models.DateField(null=True, blank=True, verbose_name='Дата зачисления')
    left_at = models.DateField(null=True, blank=True, verbose_name='Дата выбытия')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    invited_to_account = models.BooleanField(default=False, verbose_name='Приглашён в аккаунт')
    account_registered = models.BooleanField(default=False, verbose_name='Аккаунт зарегистрирован')
    progress_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='Прогресс (%)'
    )
    rating = models.DecimalField(max_digits=4, decimal_places=2, default=0, verbose_name='Рейтинг')
    points = models.PositiveIntegerField(default=0, verbose_name='Баллы')
    note = models.TextField(blank=True, verbose_name='Примечание')

    class Meta:
        verbose_name = 'Студент курса'
        verbose_name_plural = 'Студенты курса'
        unique_together = ('course', 'student')
        ordering = ['student__full_name']

    def __str__(self):
        return f'{self.student} — {self.course}'

    @property
    def paid_months(self):
        """Получить количество оплаченных месяцев"""
        from apps.payments.models import Payment
        
        # Получаем все оплаты для этого студента на этот курс
        payments = Payment.objects.filter(
            student=self.student,
            course=self.course
        ).aggregate(
            total_months=Sum('month_count')
        )
        
        return payments['total_months'] or 0

    @property
    def is_paid(self):
        """Проверить, есть ли хотя бы одна оплата"""
        from apps.payments.models import Payment
        return Payment.objects.filter(
            student=self.student,
            course=self.course
        ).exists()


# Import ticket models
from .tickets import TicketBalance, TicketTransaction, TicketAttendance, TicketTariff
