from django.db import models
from apps.core.models import TimeStampedModel


class Section(TimeStampedModel):
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='sections', verbose_name='Курс'
    )
    title = models.CharField(max_length=200, verbose_name='Название главы')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    is_visible = models.BooleanField(default=True, verbose_name='Видимая')

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class Lecture(TimeStampedModel):
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='lectures', verbose_name='Курс'
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE,
        related_name='lectures', verbose_name='Раздел',
        null=True, blank=True
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    lesson_date = models.DateField(verbose_name='Дата урока')
    start_time = models.TimeField(null=True, blank=True, verbose_name='Время начала')
    end_time = models.TimeField(null=True, blank=True, verbose_name='Время окончания')
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Запланирован'),
            ('completed', 'Завершен'),
            ('cancelled', 'Отменен'),
        ],
        default='scheduled',
        verbose_name='Статус'
    )
    temporary_mentor = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='temporary_lectures',
        verbose_name='Временный ментор'
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['lesson_date', 'start_time']

    def __str__(self):
        return f'{self.title} ({self.lesson_date})'


class Material(TimeStampedModel):
    TYPE_CHOICES = [
        ('text', 'Текст'),
        ('video', 'Видео'),
        ('file', 'Файл'),
        ('link', 'Ссылка'),
    ]

    section = models.ForeignKey(
        Section, on_delete=models.CASCADE,
        related_name='materials', verbose_name='Раздел'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text', verbose_name='Тип')
    body_html = models.TextField(blank=True, verbose_name='Содержимое (HTML)')
    file = models.FileField(upload_to='materials/', null=True, blank=True, verbose_name='Файл')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    is_visible = models.BooleanField(default=True, verbose_name='Видимый')

    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title
