from django.db import models
from apps.core.models import TimeStampedModel


class Debt(TimeStampedModel):
    STATUS_CHOICES = [
        ('active', 'Активный долг'),
        ('paid', 'Погашен'),
        ('written_off', 'Списан'),
    ]

    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='debts', verbose_name='Студент'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='debts', verbose_name='Курс'
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Всего к оплате')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Оплачено')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    note = models.TextField(blank=True, verbose_name='Примечание')

    class Meta:
        verbose_name = 'Долг'
        verbose_name_plural = 'Долги'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} — долг {self.debt_amount}'

    @property
    def debt_amount(self):
        return self.total_amount - self.paid_amount
