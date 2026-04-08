from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, OrganizationMixin
from .models_substitute import MentorSubstitution, SubstituteAccess


class Lesson(OrganizationMixin, TimeStampedModel):
    TYPE_CHOICES = [
        ('regular', 'Обычное'),
        ('exam', 'Экзамен'),
        ('practice', 'Практика'),
        ('makeup', 'Отработка'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Запланировано'),
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('postponed', 'Перенесено'),
    ]

    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='lessons', verbose_name='Курс'
    )
    title = models.CharField(max_length=200, blank=True, verbose_name='Тема урока')
    lesson_date = models.DateField(verbose_name='Дата урока')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    room = models.CharField(max_length=100, blank=True, verbose_name='Кабинет')
    meet_link = models.URLField(blank=True, verbose_name='Ссылка на встречу')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='regular', verbose_name='Тип')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled', verbose_name='Статус')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_lessons', verbose_name='Создал'
    )
    temporary_mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='temporarily_mentoring_lessons', verbose_name='Временный ментор (замена)',
        limit_choices_to={'role': 'mentor'}
    )

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['lesson_date', 'start_time']

    def __str__(self):
        return f'{self.course} — {self.lesson_date} {self.start_time}'

    @property
    def duration_minutes(self):
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        return int((end - start).total_seconds() / 60)
    
    @property
    def current_mentor(self):
        """Возвращает актуального ментора урока (основной или временный)"""
        return self.temporary_mentor or self.course.mentor
    
    @property
    def is_substituted(self):
        """Проверяет, есть ли замена на урок"""
        return bool(self.temporary_mentor)
    
    @property
    def mentor_display(self):
        """Отображение имени ментора с учетом замены"""
        if self.temporary_mentor:
            return f"{self.temporary_mentor.get_full_name()} (замена)"
        return self.course.mentor.get_full_name()
    
    @property
    def status_color(self):
        """Возвращает цвет для статуса урока"""
        colors = {
            'scheduled': 'primary',
            'completed': 'success', 
            'cancelled': 'danger',
            'postponed': 'warning'
        }
        return colors.get(self.status, 'secondary')
