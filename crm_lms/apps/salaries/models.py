from django.db import models
from apps.core.models import TimeStampedModel


class SalaryAccrual(TimeStampedModel):
    PAID_STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('paid', 'Выплачено'),
        ('cancelled', 'Отменено'),
    ]

    mentor = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.CASCADE,
        related_name='salary_accruals', verbose_name='Ментор',
        limit_choices_to={'role': 'mentor'}
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='salary_accruals', verbose_name='Курс'
    )
    month = models.DateField(verbose_name='Месяц')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    paid_status = models.CharField(
        max_length=15, choices=PAID_STATUS_CHOICES, default='pending', verbose_name='Статус выплаты'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    class Meta:
        verbose_name = 'Начисление зарплаты'
        verbose_name_plural = 'Начисления зарплат'
        ordering = ['-month']

    def __str__(self):
        return f'{self.mentor} — {self.month.strftime("%B %Y")} — {self.amount}'
