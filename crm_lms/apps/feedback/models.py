from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Feedback(models.Model):
    """Модель для хранения обратной связи"""
    
    FEEDBACK_TYPES = (
        ('review', 'Отзыв'),
        ('idea', 'Идея'),
        ('bug', 'Баг'),
        ('complaint', 'Жалоба'),
        ('suggestion', 'Предложение'),
    )
    
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('resolved', 'Решено'),
        ('closed', 'Закрыто'),
    )
    
    type = models.CharField(
        max_length=20, 
        choices=FEEDBACK_TYPES,
        verbose_name='Тип обратной связи'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Пользователь'
    )
    telegram_sent = models.BooleanField(
        default=False,
        verbose_name='Отправлено в Telegram'
    )
    telegram_message_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='ID сообщения в Telegram'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"
    
    def get_user_display(self):
        if self.user:
            return self.user.username
        return 'Аноним'
