from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Информация'),
        ('success', 'Успех'),
        ('warning', 'Предупреждение'),
        ('error', 'Ошибка'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications', verbose_name='Получатель'
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    link = models.CharField(max_length=500, blank=True, verbose_name='Ссылка')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient} - {self.title}'

    @classmethod
    def create_notification(cls, recipient, title, message, type='info', link=''):
        """Создать уведомление"""
        return cls.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            type=type,
            link=link
        )

    @classmethod
    def homework_accepted(cls, student, homework_title, link=''):
        """Уведомление о принятии домашки"""
        title = "Решение принято"
        message = f'Ваше решение задания "{homework_title}" было принято'
        return cls.create_notification(
            recipient=student,
            title=title,
            message=message,
            type='success',
            link=link
        )

    @classmethod
    def homework_rejected(cls, student, homework_title, reason='', link=''):
        """Уведомление об отклонении домашки"""
        title = "Решение отклонено"
        message = f'Ваше решение задания "{homework_title}" было отклонено'
        if reason:
            message += f'. Причина: {reason}'
        return cls.create_notification(
            recipient=student,
            title=title,
            message=message,
            type='warning',
            link=link
        )

    @classmethod
    def payment_reminder(cls, student, course_title, due_date, link=''):
        """Уведомление о необходимости оплаты"""
        title = "Пора оплатить курс"
        message = f'Необходимо оплатить курс "{course_title}" до {due_date}'
        return cls.create_notification(
            recipient=student,
            title=title,
            message=message,
            type='warning',
            link=link
        )

    @classmethod
    def new_homework(cls, mentor, course_title, homework_title, link=''):
        """Уведомление ментору о новой домашке"""
        title = "Новое задание на проверку"
        message = f'Новое задание "{homework_title}" от студента курса "{course_title}"'
        return cls.create_notification(
            recipient=mentor,
            title=title,
            message=message,
            type='info',
            link=link
        )

    @classmethod
    def course_completed(cls, student, course_title, link=''):
        """Уведомление о завершении курса"""
        title = "Курс завершен"
        message = f'Поздравляем! Вы завершили курс "{course_title}"'
        return cls.create_notification(
            recipient=student,
            title=title,
            message=message,
            type='success',
            link=link
        )
