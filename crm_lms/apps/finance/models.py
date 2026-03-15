from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class FinanceCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    type = models.CharField(max_length=10, choices=[('income', 'Доход'), ('expense', 'Расход')], verbose_name='Тип')
    color = models.CharField(max_length=7, default='#6366f1', verbose_name='Цвет')

    class Meta:
        verbose_name = 'Категория финансов'
        verbose_name_plural = 'Категории финансов'

    def __str__(self):
        return self.name


class FinanceAccount(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название счёта')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Баланс')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'

    def __str__(self):
        return f'{self.name} ({self.balance})'


class FinanceTransaction(TimeStampedModel):
    TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
        ('transfer', 'Перевод'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Тип')
    category = models.ForeignKey(
        FinanceCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions', verbose_name='Категория'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    account = models.ForeignKey(
        FinanceAccount, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions', verbose_name='Счёт'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    transaction_date = models.DateField(verbose_name='Дата транзакции')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='finance_transactions', verbose_name='Кто добавил'
    )

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-transaction_date']

    def __str__(self):
        return f'{self.get_type_display()} — {self.amount} ({self.transaction_date})'
