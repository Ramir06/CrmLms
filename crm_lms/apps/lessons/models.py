from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Lesson(TimeStampedModel):
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
