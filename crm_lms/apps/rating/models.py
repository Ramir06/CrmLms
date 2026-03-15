from django.db import models
from apps.core.models import TimeStampedModel


class StudentRating(TimeStampedModel):
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='ratings', verbose_name='Курс'
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='ratings', verbose_name='Студент'
    )
    total_score = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Общий балл')
    attendance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Балл посещаемости')
    assignment_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Балл заданий')
    rank = models.PositiveSmallIntegerField(default=0, verbose_name='Место в рейтинге')

    class Meta:
        verbose_name = 'Рейтинг студента'
        verbose_name_plural = 'Рейтинги студентов'
        unique_together = ('course', 'student')
        ordering = ['-total_score']

    def __str__(self):
        return f'{self.student} — {self.course} — {self.total_score}'
