from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    METHOD_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('transfer', 'Перевод'),
        ('online', 'Онлайн'),
    ]

    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='payments', verbose_name='Студент'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='payments', verbose_name='Курс'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    payment_method = models.CharField(
        max_length=10, choices=METHOD_CHOICES, default='cash', verbose_name='Способ оплаты'
    )
    paid_at = models.DateField(verbose_name='Дата оплаты')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_payments', verbose_name='Кто добавил'
    )

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.student} — {self.amount} ({self.paid_at})'
