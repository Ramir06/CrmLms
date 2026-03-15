from django.db import models
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

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        unique_together = ('lesson', 'student')

    def __str__(self):
        return f'{self.student} — {self.lesson} — {self.get_attendance_status_display()}'
