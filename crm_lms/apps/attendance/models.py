from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
        ('excused', 'Уважительная'),
    ]

    lesson = models.ForeignKey(
        'lessons.Lesson', on_delete=models.CASCADE,
        related_name='attendance_records', verbose_name='Занятие'
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='attendance_records', verbose_name='Студент'
    )
    attendance_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='absent', verbose_name='Статус посещения'
    )
    mark_time = models.DateTimeField(auto_now=True, verbose_name='Время отметки')
    comment = models.CharField(max_length=300, blank=True, verbose_name='Комментарий')
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='marked_attendance', verbose_name='Кто отметил'
    )
    color_status = models.CharField(max_length=20, blank=True, default='', verbose_name='Цветовой статус')

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        unique_together = ('lesson', 'student')

    def __str__(self):
        return f'{self.student} — {self.lesson} — {self.get_attendance_status_display()}'

    @property
    def marked_by_display(self):
        """Отображение того, кто отметил посещаемость"""
        if self.marked_by:
            if self.marked_by == self.lesson.course.mentor:
                return f"{self.marked_by.get_display_name()} (основной ментор)"
            else:
                return f"{self.marked_by.get_display_name()} (замена)"
        return "Система"
