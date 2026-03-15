from django.db import models
from apps.core.models import TimeStampedModel


class Course(TimeStampedModel):
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

    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
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
    days_of_week = models.CharField(
        max_length=20, choices=DAY_CHOICES, default='mon_wed_fri', verbose_name='Дни занятий'
    )
    lesson_start_time = models.TimeField(null=True, blank=True, verbose_name='Время начала')
    lesson_end_time = models.TimeField(null=True, blank=True, verbose_name='Время окончания')
    capacity = models.PositiveSmallIntegerField(default=15, verbose_name='Вместимость')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_unlimited = models.BooleanField(default=False, verbose_name='Бесконечный курс')
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')
    color = models.CharField(max_length=7, default='#7c3aed', verbose_name='Цвет (HEX)')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            self.slug = slugify(self.title) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    @property
    def current_students_count(self):
        return self.course_students.filter(status='active').count()

    @property
    def fill_display(self):
        return f'{self.current_students_count}/{self.capacity}'

    def get_days_display_short(self):
        return dict(self.DAY_CHOICES).get(self.days_of_week, self.days_of_week)


class CourseStudent(TimeStampedModel):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('left', 'Выбыл'),
        ('frozen', 'Заморожен'),
        ('graduated', 'Окончил'),
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


# Import ticket models
from .tickets import TicketBalance, TicketTransaction, TicketAttendance
