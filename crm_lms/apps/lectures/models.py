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
