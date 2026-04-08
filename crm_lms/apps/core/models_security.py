from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class FailedLoginAttempt(models.Model):
    """Запись неудачной попытки входа"""
    
    username = models.CharField(max_length=150, verbose_name='Имя пользователя')
    ip_address = models.GenericIPAddressField(verbose_name='IP адрес')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время попытки')
    
    class Meta:
        verbose_name = 'Неудачная попытка входа'
        verbose_name_plural = 'Неудачные попытки входа'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.username} - {self.timestamp}"


class AccountLock(models.Model):
    """Блокировка аккаунта"""
    
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='account_lock',
        verbose_name='Пользователь'
    )
    locked_at = models.DateTimeField(auto_now_add=True, verbose_name='Время блокировки')
    lock_reason = models.CharField(
        max_length=255,
        default='Too many failed login attempts',
        verbose_name='Причина блокировки'
    )
    unlock_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        verbose_name='Токен разблокировки'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    
    class Meta:
        verbose_name = 'Блокировка аккаунта'
        verbose_name_plural = 'Блокировки аккаунтов'
    
    def __str__(self):
        return f"Блокировка {self.user.username} с {self.locked_at}"
    
    @property
    def is_expired(self):
        """Проверяет, истек ли срок блокировки (24 часа)"""
        return self.locked_at < timezone.now() - timedelta(hours=24)
    
    def unlock(self):
        """Разблокировать аккаунт"""
        self.is_active = False
        self.save()
    
    def extend_lock(self):
        """Продлить блокировку еще на 24 часа"""
        self.locked_at = timezone.now()
        self.save()
