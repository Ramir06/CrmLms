from django.db import models
from django.conf import settings
from apps.organizations.models import Organization


class Event(models.Model):
    TARGET_CHOICES = [
        ('mentor', 'Ментор'),
        ('student', 'Студент'),
        ('admin', 'Администратор'),
        ('organization', 'Общая организация'),
        ('custom', 'Кому либо'),
    ]
    
    COLOR_CHOICES = [
        ('#28a745', 'Зеленый'),
        ('#dc3545', 'Красный'),
        ('#007bff', 'Синий'),
        ('#ffc107', 'Желтый'),
        ('#6f42c1', 'Фиолетовый'),
        ('#fd7e14', 'Оранжевый'),
        ('#20c997', 'Бирюзовый'),
        ('#e83e8c', 'Розовый'),
        ('#6c757d', 'Серый'),
        ('#343a40', 'Темный'),
    ]
    
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Начало')
    end_time = models.TimeField(verbose_name='Конец')
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, verbose_name='Для кого')
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Конкретный пользователь',
        related_name='events'
    )
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#28a745', verbose_name='Цвет')
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        verbose_name='Организация'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events',
        verbose_name='Кто создал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.title} - {self.date}"
