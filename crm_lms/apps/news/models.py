from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class News(TimeStampedModel):
    AUDIENCE_CHOICES = [
        ('all', 'Все'),
        ('admins', 'Администраторы'),
        ('mentors', 'Менторы'),
        ('students', 'Студенты'),
    ]

    title = models.CharField(max_length=300, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержимое')
    image = models.ImageField(upload_to='news/', null=True, blank=True, verbose_name='Изображение')
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='all', verbose_name='Аудитория')
    is_published = models.BooleanField(default=False, verbose_name='Опубликовано')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата публикации')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_news', verbose_name='Автор'
    )
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE, null=True, blank=True,
        verbose_name='Организация'
    )

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
