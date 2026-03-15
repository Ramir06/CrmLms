from django.db import models
from apps.core.models import TimeStampedModel


class Student(TimeStampedModel):
    GENDER_CHOICES = [('male', 'Мужской'), ('female', 'Женский')]
    SOURCE_CHOICES = [
        ('instagram', 'Instagram'), ('telegram', 'Telegram'),
        ('referral', 'Реферал'), ('website', 'Сайт'), ('other', 'Другое'),
    ]
    STATUS_CHOICES = [
        ('active', 'Активный'), ('inactive', 'Неактивный'),
        ('graduated', 'Окончил'), ('expelled', 'Отчислен'),
        ('left', 'Ушедший'),
    ]

    full_name = models.CharField(max_length=200, verbose_name='Полное имя')
    first_name = models.CharField(max_length=100, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    parent_name = models.CharField(max_length=200, blank=True, verbose_name='Имя родителя')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон родителя')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name='Пол')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, verbose_name='Источник')
    note = models.TextField(blank=True, verbose_name='Примечание')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    user_account = models.OneToOneField(
        'accounts.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='student_profile',
        verbose_name='Аккаунт пользователя'
    )

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def get_active_courses(self):
        return self.course_enrollments.filter(status='active').select_related('course')
