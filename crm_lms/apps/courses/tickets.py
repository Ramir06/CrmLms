from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel, OrganizationMixin


class TicketTariff(OrganizationMixin, TimeStampedModel):
    """Тарифы для талонов"""
    title = models.CharField(
        max_length=200, 
        verbose_name='Название тарифа'
    )
    lessons_count = models.PositiveIntegerField(
        verbose_name='Количество занятий'
    )
    price_per_lesson = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Цена за занятие'
    )
    total_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        editable=False,
        verbose_name='Общая стоимость'
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name='Активен'
    )
    description = models.TextField(
        blank=True, 
        verbose_name='Описание'
    )

    class Meta:
        verbose_name = 'Тариф талонов'
        verbose_name_plural = 'Тарифы талонов'
        ordering = ['lessons_count']

    def save(self, *args, **kwargs):
        self.total_price = self.lessons_count * self.price_per_lesson
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} - {self.lessons_count} зан. ({self.total_price} сом)'


class TicketBalance(models.Model):
    """Баланс талонов студента"""
    enrollment = models.OneToOneField(
        'CourseStudent', 
        on_delete=models.CASCADE, 
        related_name='ticket_balance',
        verbose_name='Зачисление'
    )
    total_tickets = models.PositiveIntegerField(
        default=0, 
        verbose_name='Всего талонов'
    )
    used_tickets = models.PositiveIntegerField(
        default=0, 
        verbose_name='Использовано талонов'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Обновлен'
    )

    class Meta:
        verbose_name = 'Баланс талонов'
        verbose_name_plural = 'Балансы талонов'

    @property
    def remaining_tickets(self):
        """Оставшиеся талоны"""
        return max(0, self.total_tickets - self.used_tickets)

    def __str__(self):
        return f'{self.enrollment.student.full_name} - {self.remaining_tickets}/{self.total_tickets}'


class TicketTransaction(models.Model):
    """Транзакции с талонами"""
    TRANSACTION_TYPES = [
        ('add', 'Добавление'),
        ('consume', 'Списание'),
        ('adjust', 'Корректировка'),
    ]

    enrollment = models.ForeignKey(
        'CourseStudent', 
        on_delete=models.CASCADE, 
        related_name='ticket_transactions',
        verbose_name='Зачисление'
    )
    transaction_type = models.CharField(
        max_length=10, 
        choices=TRANSACTION_TYPES,
        default='add',
        verbose_name='Тип транзакции'
    )
    quantity = models.IntegerField(
        verbose_name='Количество'
    )
    price_per_ticket = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        null=True, 
        blank=True,
        verbose_name='Цена за талон'
    )
    comment = models.TextField(
        blank=True, 
        verbose_name='Комментарий'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Создан'
    )
    created_by = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Создал'
    )

    class Meta:
        verbose_name = 'Транзакция талонов'
        verbose_name_plural = 'Транзакции талонов'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_transaction_type_display()} {self.quantity} талонов'


class TicketAttendance(models.Model):
    """Посещаемость по талонам"""
    enrollment = models.ForeignKey(
        'CourseStudent', 
        on_delete=models.CASCADE, 
        related_name='ticket_attendances',
        verbose_name='Зачисление'
    )
    lesson_date = models.DateField(
        verbose_name='Дата занятия'
    )
    lessons_count = models.PositiveIntegerField(
        default=1, 
        verbose_name='Количество занятий'
    )
    marked_by = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Отметил'
    )
    comment = models.TextField(
        blank=True, 
        verbose_name='Комментарий'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Создан'
    )

    class Meta:
        verbose_name = 'Посещение по талонам'
        verbose_name_plural = 'Посещения по талонам'
        ordering = ['-lesson_date']

    def __str__(self):
        return f'{self.enrollment.student.full_name} - {self.lesson_date} ({self.lessons_count} зан.)'
