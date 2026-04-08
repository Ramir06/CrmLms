from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.settings.models import PaymentMethod


class OrganizationReceipt(TimeStampedModel):
    """Данные организации для формирования чеков"""
    organization_name = models.CharField(max_length=255, verbose_name='Название организации')
    organization_type = models.CharField(
        max_length=20, 
        choices=[
            ('ИП', 'ИП'),
            ('ООО', 'ООО'),
            ('ОССО', 'ОССО'),
        ],
        default='ИП',
        verbose_name='Тип организации'
    )
    inn = models.CharField(max_length=12, verbose_name='ИНН')
    tax_per_receipt = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name='Налог с каждого чека (%)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Данные для чека'
        verbose_name_plural = 'Данные для чеков'
    
    def __str__(self):
        return f'{self.organization_type} {self.organization_name}'
    
    @classmethod
    def get_active(cls):
        """Получить активные данные организации"""
        try:
            return cls.objects.filter(is_active=True).first()
        except Exception:
            return None


class Payment(TimeStampedModel):
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='payments', verbose_name='Студент'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='payments', verbose_name='Курс'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.SET_NULL, null=True, 
        verbose_name='Способ оплаты'
    )
    paid_at = models.DateField(verbose_name='Дата оплаты')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_payments', verbose_name='Кто добавил'
    )
    # Новые поля для помесячной оплаты
    months_paid = models.JSONField(default=list, verbose_name='Оплаченные месяцы')
    month_count = models.PositiveIntegerField(default=1, verbose_name='Количество месяцев курса')
    # Поле для формирования чека
    generate_receipt = models.BooleanField(default=False, verbose_name='Сформировать чек об оплате')

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.student} — {self.amount} ({self.paid_at})'
    
    @property
    def payment_method_name(self):
        """Возвращает название способа оплаты для совместимости."""
        return self.payment_method.name if self.payment_method else 'Не указан'
