from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from apps.core.models import TimeStampedModel


class SystemSetting(models.Model):
    """Global system settings."""
    key = models.CharField(max_length=100, unique=True, help_text="Setting key")
    value = models.TextField(blank=True, help_text="Setting value")
    description = models.TextField(blank=True, help_text="Description")
    is_public = models.BooleanField(default=False, help_text="Whether this setting is visible to non-admins")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Системная настройка"
        verbose_name_plural = "Системные настройки"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

    @classmethod
    def get_value(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def is_maintenance_mode(cls):
        return cls.get_value('maintenance_mode', 'false').lower() == 'true'


class FooterContent(TimeStampedModel):
    """Контент футера для редактирования через админ панель."""
    title = models.CharField(max_length=200, blank=True, verbose_name="Заголовок футера")
    description = models.TextField(blank=True, verbose_name="Описание футера")
    contact_info = models.TextField(blank=True, verbose_name="Контактная информация")
    social_links = models.JSONField(default=dict, blank=True, verbose_name="Социальные сети", 
                              help_text="JSON формат: {'telegram': 'url', 'instagram': 'url'}")
    additional_links = models.JSONField(default=dict, blank=True, verbose_name="Дополнительные ссылки", 
                                   help_text="JSON формат: {'Название': 'url'}")
    public_offer = models.TextField(blank=True, verbose_name="Публичная оферта")
    copyright_text = models.CharField(max_length=500, blank=True, default='', verbose_name="Текст копирайта")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    class Meta:
        verbose_name = "Контент футера"
        verbose_name_plural = "Контент футера"
    
    def __str__(self):
        return self.title or "Настройки футера"


class FooterNavigationLink(TimeStampedModel):
    """Навигационные ссылки в футере."""
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL идентификатор")
    title = models.CharField(max_length=200, verbose_name="Название ссылки")
    content = models.TextField(blank=True, verbose_name="Содержимое")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")
    
    class Meta:
        verbose_name = "Навигационная ссылка футера"
        verbose_name_plural = "Навигационные ссылки футера"
        ordering = ['order', 'title']
    
    def __str__(self):
        return self.title


class SectionOrder(models.Model):
    """Custom ordering for course sections."""
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    section = models.ForeignKey('lectures.Section', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Порядок раздела"
        verbose_name_plural = "Порядки разделов"
        unique_together = ['course', 'section']
        ordering = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.section.title} ({self.order})"


class PaymentMethod(TimeStampedModel):
    """Способы оплаты для управления в супер-админ панели."""
    name = models.CharField(max_length=100, verbose_name='Название способа оплаты')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    description = models.TextField(blank=True, verbose_name='Описание')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    
    class Meta:
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
