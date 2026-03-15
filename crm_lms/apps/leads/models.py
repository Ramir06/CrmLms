from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Lead(TimeStampedModel):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('consultation', 'Консультация'),
        ('trial_lesson', 'Пробный урок'),
        ('no_show', 'Не пришёл'),
        ('enrolling', 'Зачисление'),
        ('rejected', 'Отказ'),
    ]
    SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('referral', 'Реферал'),
        ('website', 'Сайт'),
        ('vk', 'ВКонтакте'),
        ('other', 'Другое'),
    ]

    full_name = models.CharField(max_length=200, verbose_name='Полное имя')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, verbose_name='Источник')
    interested_course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='leads', verbose_name='Интересующий курс'
    )
    channel = models.CharField(max_length=100, blank=True, verbose_name='Канал')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads', verbose_name='Ответственный'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    note = models.TextField(blank=True, verbose_name='Примечание')
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')

    class Meta:
        verbose_name = 'Лид'
        verbose_name_plural = 'Лиды'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} ({self.phone})'


class LeadAction(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='actions', verbose_name='Лид')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        verbose_name='Кто выполнил'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Действие с лидом'
        verbose_name_plural = 'Действия с лидами'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.lead} → {self.new_status}'
