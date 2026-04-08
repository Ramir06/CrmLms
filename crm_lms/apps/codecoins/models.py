from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.accounts.models import CustomUser
from apps.courses.models import Course, CourseStudent


class CoinWallet(TimeStampedModel):
    """Кошелек кодкойнов студента"""
    student = models.OneToOneField(
        'students.Student', on_delete=models.CASCADE,
        related_name='coin_wallet', verbose_name='Студент'
    )
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Баланс кодкойнов'
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        verbose_name = 'Кошелек кодкойнов'
        verbose_name_plural = 'Кошельки кодкойнов'

    def __str__(self):
        return f'{self.student.full_name}: {self.balance} кодкойнов'


class CoinTransaction(TimeStampedModel):
    """Транзакция кодкойнов"""
    TRANSACTION_TYPES = [
        ('income', 'Начисление'),
        ('expense', 'Списание'),
        ('withdrawal_request', 'Заявка на вывод'),
        ('withdrawal_approved', 'Вывод подтвержден'),
        ('withdrawal_rejected', 'Вывод отклонен'),
        ('correction', 'Корректировка'),
        ('mentor_mass_accrual', 'Массовое начисление ментором'),
    ]

    wallet = models.ForeignKey(
        CoinWallet, on_delete=models.CASCADE,
        related_name='transactions', verbose_name='Кошелек'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Сумма'
    )
    transaction_type = models.CharField(
        max_length=30, choices=TRANSACTION_TYPES,
        verbose_name='Тип операции'
    )
    description = models.TextField(verbose_name='Описание')
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coin_transactions_created', verbose_name='Кто создал'
    )
    course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coin_transactions', verbose_name='Курс'
    )
    mentor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coin_transactions_mentor', verbose_name='Ментор',
        limit_choices_to={'role': 'mentor'}
    )
    withdrawal_request = models.OneToOneField(
        'CoinWithdrawalRequest', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='transaction',
        verbose_name='Заявка на вывод'
    )
    batch = models.ForeignKey(
        'CoinBatch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions', verbose_name='Пакет начислений'
    )
    is_cancelled = models.BooleanField(default=False, verbose_name='Отменена')
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name='Отменена в')
    cancelled_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coin_transactions_cancelled', verbose_name='Отменил'
    )

    class Meta:
        verbose_name = 'Транзакция кодкойнов'
        verbose_name_plural = 'Транзакции кодкойнов'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.wallet.student} - {self.amount} ({self.transaction_type})'

    def clean(self):
        if self.amount <= 0 and self.transaction_type not in ['expense', 'withdrawal_approved']:
            raise ValidationError('Сумма должна быть положительной для доходных операций')
        if self.amount >= 0 and self.transaction_type in ['expense', 'withdrawal_approved']:
            raise ValidationError('Сумма должна быть отрицательной для расходных операций')

    @property
    def is_income(self):
        return self.amount > 0

    @property
    def is_expense(self):
        return self.amount < 0


class CoinWithdrawalSetting(TimeStampedModel):
    """Настройки вывода кодкойнов"""
    is_open = models.BooleanField(default=False, verbose_name='Вывод открыт')
    next_open_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Следующее открытие'
    )
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coin_withdrawal_settings_updated', verbose_name='Обновил'
    )

    class Meta:
        verbose_name = 'Настройка вывода кодкойнов'
        verbose_name_plural = 'Настройки вывода кодкойнов'

    def __str__(self):
        status = 'открыт' if self.is_open else 'закрыт'
        return f'Вывод {status}'


class CoinWithdrawalRequest(TimeStampedModel):
    """Заявка на вывод кодкойнов"""
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Подтверждена'),
        ('rejected', 'Отклонена'),
    ]
    PAYOUT_METHODS = [
        ('mbank', 'МБАНК'),
        ('phone_balance', 'Баланс телефона'),
    ]

    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='coin_withdrawal_requests', verbose_name='Студент'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Сумма'
    )
    payout_method = models.CharField(
        max_length=20, choices=PAYOUT_METHODS,
        verbose_name='Способ вывода'
    )
    phone_number = models.CharField(
        max_length=20, verbose_name='Номер телефона'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', verbose_name='Статус'
    )
    reviewed_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coin_withdrawal_requests_reviewed', verbose_name='Обработал'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Обработана в')
    rejection_reason = models.TextField(blank=True, verbose_name='Причина отклонения')

    class Meta:
        verbose_name = 'Заявка на вывод кодкойнов'
        verbose_name_plural = 'Заявки на вывод кодкойнов'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.full_name} - {self.amount} ({self.status})'

    def clean(self):
        if self.amount <= 0:
            raise ValidationError('Сумма должна быть положительной')
        if not self.phone_number or len(self.phone_number) < 10:
            raise ValidationError('Введите корректный номер телефона')


class CoinScale(TimeStampedModel):
    """Шкала начисления кодкойнов"""
    title = models.CharField(max_length=100, verbose_name='Название')
    value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Значение в кодкойнах'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Шкала кодкойнов'
        verbose_name_plural = 'Шкалы кодкойнов'
        ordering = ['sort_order', 'title']

    def __str__(self):
        return f'{self.title}: {self.value} кодкойнов'


class CoinBatch(TimeStampedModel):
    """Пакет массовых начислений"""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='coin_batches', verbose_name='Курс'
    )
    mentor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coin_batches_created', verbose_name='Ментор',
        limit_choices_to={'role': 'mentor'}
    )
    lesson_date = models.DateField(verbose_name='Дата урока')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    class Meta:
        verbose_name = 'Пакет начислений кодкойнов'
        verbose_name_plural = 'Пакеты начислений кодкойнов'
        ordering = ['-lesson_date', '-created_at']

    def __str__(self):
        return f'{self.course.title} - {self.lesson_date}'


class CoinBatchItem(TimeStampedModel):
    """Элемент пакета начислений"""
    batch = models.ForeignKey(
        CoinBatch, on_delete=models.CASCADE,
        related_name='items', verbose_name='Пакет'
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='coin_batch_items', verbose_name='Студент'
    )
    scale = models.ForeignKey(
        CoinScale, on_delete=models.CASCADE,
        related_name='batch_items', verbose_name='Шкала'
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Сумма'
    )
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Элемент начисления кодкойнов'
        verbose_name_plural = 'Элементы начисления кодкойнов'
        unique_together = ('batch', 'student', 'scale')
        ordering = ['batch', 'student__full_name']

    def __str__(self):
        return f'{self.student.full_name} - {self.scale.title}: {self.amount}'
