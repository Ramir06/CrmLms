from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class ChatRoom(TimeStampedModel):
    """Комната чата для общего общения"""
    name = models.CharField(max_length=100, verbose_name='Название комнаты')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    
    class Meta:
        verbose_name = 'Комната чата'
        verbose_name_plural = 'Комнаты чата'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ChatMessage(TimeStampedModel):
    """Сообщение в чате"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name='Комната')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
        related_name='chat_messages', verbose_name='Автор'
    )
    content = models.TextField(verbose_name='Содержание')
    is_pinned = models.BooleanField(default=False, verbose_name='Закреплено')
    is_edited = models.BooleanField(default=False, verbose_name='Отредактировано')
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name='Время редактирования')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Время удаления')
    
    class Meta:
        verbose_name = 'Сообщение чата'
        verbose_name_plural = 'Сообщения чата'
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['room', '-is_pinned', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.author.get_display_name()}: {self.content[:50]}...'
    
    @property
    def display_content(self):
        """Отображаемое содержание (с учетом удаления)"""
        if self.is_deleted:
            return '[Сообщение удалено]'
        return self.content
    
    @property
    def can_edit(self):
        """Можно ли редактировать сообщение"""
        from datetime import timedelta
        from django.utils import timezone
        return not self.is_deleted and (timezone.now() - self.created_at) < timedelta(hours=1)
    
    @property
    def can_delete(self):
        """Можно ли удалить сообщение"""
        from datetime import timedelta
        from django.utils import timezone
        return not self.is_deleted and (timezone.now() - self.created_at) < timedelta(hours=24)


class ChatReadStatus(TimeStampedModel):
    """Статус прочтения сообщений"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='chat_read_status', verbose_name='Пользователь'
    )
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='read_status', verbose_name='Комната')
    last_read_message = models.ForeignKey(
        ChatMessage, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='read_by', verbose_name='Последнее прочитанное сообщение'
    )
    
    class Meta:
        verbose_name = 'Статус прочтения'
        verbose_name_plural = 'Статусы прочтения'
        unique_together = ('user', 'room')
        indexes = [
            models.Index(fields=['user', 'room']),
        ]
    
    def __str__(self):
        return f'{self.user.get_display_name()} - {self.room.name}'


class ChatAttachment(TimeStampedModel):
    """Вложения в сообщениях чата"""
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE,
        related_name='attachments', verbose_name='Сообщение'
    )
    file = models.FileField(upload_to='chat_attachments/', verbose_name='Файл')
    filename = models.CharField(max_length=255, verbose_name='Имя файла')
    file_size = models.PositiveIntegerField(verbose_name='Размер файла (байты)')
    mime_type = models.CharField(max_length=100, verbose_name='MIME тип')
    
    class Meta:
        verbose_name = 'Вложение чата'
        verbose_name_plural = 'Вложения чата'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.filename} ({self.file_size} bytes)'

    @property
    def file_size_display(self):
        """Отображение размера файла"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
