from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


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
