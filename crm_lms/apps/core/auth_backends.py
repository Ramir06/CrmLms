from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models_security import FailedLoginAttempt, AccountLock
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SecureAuthenticationBackend(ModelBackend):
    """
    Безопасный бэкенд аутентификации с блокировкой после 3 неудачных попыток
    """
    
    MAX_FAILED_ATTEMPTS = 3
    LOCK_DURATION_HOURS = 24
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Записываем неудачную попытку
            self._record_failed_attempt(username, request)
            return None
        
        # Проверяем, не заблокирован ли аккаунт
        if self._is_account_locked(user):
            logger.warning(f"Login attempt on locked account: {username}")
            return None
        
        # Проверяем пароль
        if user.check_password(password) and self.user_can_authenticate(user):
            # Успешный вход - сбрасываем счетчик неудачных попыток
            self._clear_failed_attempts(username)
            
            # Обновляем время последнего входа
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            
            return user
        else:
            # Неудачная попытка - записываем и проверяем блокировку
            self._record_failed_attempt(username, request)
            self._check_and_lock_account(user)
            return None
    
    def _record_failed_attempt(self, username, request):
        """Записывает неудачную попытку входа"""
        try:
            from .models_security import FailedLoginAttempt
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            FailedLoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.warning(f"Failed login attempt for {username} from {ip_address}")
        except Exception as e:
            # Если модели еще не созданы, просто логируем
            logger.error(f"Error recording failed attempt: {e}")
    
    def _clear_failed_attempts(self, username):
        """Очищает неудачные попытки после успешного входа"""
        try:
            from .models_security import FailedLoginAttempt
            FailedLoginAttempt.objects.filter(username=username).delete()
        except Exception as e:
            # Если модели еще не созданы, игнорируем
            logger.error(f"Error clearing failed attempts: {e}")
    
    def _get_failed_attempts_count(self, username):
        """Возвращает количество неудачных попыток за последние 15 минут"""
        try:
            from .models_security import FailedLoginAttempt
            fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)
            return FailedLoginAttempt.objects.filter(
                username=username,
                timestamp__gte=fifteen_minutes_ago
            ).count()
        except Exception as e:
            # Если модели еще не созданы, возвращаем 0
            logger.error(f"Error getting failed attempts count: {e}")
            return 0
    
    def _is_account_locked(self, user):
        """Проверяет, заблокирован ли аккаунт"""
        try:
            from .models_security import AccountLock
            lock = AccountLock.objects.filter(user=user, is_active=True).first()
            if lock and not lock.is_expired:
                return True
            elif lock and lock.is_expired:
                # Автоматически разблокируем истекшие блокировки
                lock.unlock()
                return False
        except Exception as e:
            # Если модели еще не созданы, считаем что аккаунт не заблокирован
            logger.error(f"Error checking account lock: {e}")
        return False
    
    def _check_and_lock_account(self, user):
        """Проверяет и блокирует аккаунт при необходимости"""
        try:
            from .models_security import AccountLock
            failed_count = self._get_failed_attempts_count(user.username)
            
            if failed_count >= self.MAX_FAILED_ATTEMPTS:
                # Блокируем аккаунт
                lock, created = AccountLock.objects.get_or_create(
                    user=user,
                    defaults={
                        'lock_reason': f'Too many failed login attempts ({failed_count} attempts)',
                        'unlock_token': self._generate_unlock_token()
                    }
                )
                
                if created:
                    logger.error(f"Account {user.username} locked due to {failed_count} failed attempts")
                else:
                    # Продлеваем существующую блокировку
                    lock.extend_lock()
                    logger.error(f"Account {user.username} lock extended due to {failed_count} failed attempts")
        except Exception as e:
            # Если модели еще не созданы, просто логируем
            logger.error(f"Error checking and locking account: {e}")
    
    def _get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _generate_unlock_token(self):
        """Генерирует токен разблокировки"""
        import secrets
        return secrets.token_urlsafe(48)


def is_account_locked(user):
    """
    Проверяет, заблокирован ли аккаунт (для использования в views)
    """
    backend = SecureAuthenticationBackend()
    return backend._is_account_locked(user)


def get_failed_attempts_count(username):
    """
    Возвращает количество неудачных попыток входа
    """
    backend = SecureAuthenticationBackend()
    return backend._get_failed_attempts_count(username)


def unlock_account(user):
    """
    Разблокировать аккаунт
    """
    try:
        from .models_security import AccountLock
        lock = AccountLock.objects.filter(user=user, is_active=True).first()
        if lock:
            lock.unlock()
            logger.info(f"Account {user.username} unlocked by administrator")
            return True
    except Exception as e:
        logger.error(f"Error unlocking account: {e}")
    return False


def get_account_lock_info(user):
    """
    Возвращает информацию о блокировке аккаунта
    """
    try:
        from .models_security import AccountLock
        lock = AccountLock.objects.filter(user=user, is_active=True).first()
        if lock:
            return {
                'locked_at': lock.locked_at,
                'lock_reason': lock.lock_reason,
                'is_expired': lock.is_expired,
                'unlock_token': lock.unlock_token
            }
    except Exception as e:
        logger.error(f"Error getting account lock info: {e}")
    return None
