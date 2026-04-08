# Система безопасности: Блокировка аккаунтов

## Описание

Добавлена система защиты от подбора паролей, которая автоматически блокирует аккаунты после 3 неудачных попыток входа. Только администраторы могут разблокировать аккаунты.

## Функционал

### 🚫 **Автоматическая блокировка**
- **3 неудачные попытки** → блокировка на 24 часа
- **Запись всех попыток** с IP адресом и User Agent
- **Автоматическая разблокировка** через 24 часа

### 🔐 **Безопасная аутентификация**
- **Кастомный бэкенд** для проверки попыток входа
- **Защита от брутфорса** с временными интервалами
- **Логирование** всех подозрительных действий

### 🛠️ **Администрирование**
- **Дашборд безопасности** с статистикой
- **Список блокировок** с поиском и фильтрацией
- **Разблокировка** одним кликом
- **История попыток** входа

## Реализация

### 1. Модели безопасности

**Файл:** `apps/core/models_security.py`

```python
class FailedLoginAttempt(models.Model):
    """Запись неудачной попытки входа"""
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class AccountLock(models.Model):
    """Блокировка аккаунта"""
    user = models.OneToOneField('auth.User', ...)
    locked_at = models.DateTimeField(auto_now_add=True)
    lock_reason = models.CharField(max_length=255)
    unlock_token = models.CharField(max_length=64, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def is_expired(self):
        return self.locked_at < timezone.now() - timedelta(hours=24)
```

### 2. Безопасный бэкенд аутентификации

**Файл:** `apps/core/auth_backends.py`

```python
class SecureAuthenticationBackend(ModelBackend):
    MAX_FAILED_ATTEMPTS = 3
    LOCK_DURATION_HOURS = 24
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Проверка блокировки
        if self._is_account_locked(user):
            return None
        
        # Проверка пароля
        if user.check_password(password):
            self._clear_failed_attempts(username)
            return user
        else:
            self._record_failed_attempt(username, request)
            self._check_and_lock_account(user)
            return None
```

### 3. Расширение модели пользователя

**Файл:** `apps/accounts/models.py`

```python
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # ... существующие поля ...
    
    @property
    def is_locked(self):
        """Проверяет, заблокирован ли аккаунт"""
        from apps.core.auth_backends import is_account_locked
        return is_account_locked(self)
    
    def unlock_account(self):
        """Разблокировать аккаунт"""
        from apps.core.auth_backends import unlock_account
        return unlock_account(self)
```

### 4. Views для управления безопасностью

**Файл:** `apps/core/views_security.py`

```python
@login_required
def account_lock_list(request):
    """Список заблокированных аккаунтов"""
    if not request.user.role in ('admin', 'superadmin'):
        return redirect('dashboard:index')
    locks = AccountLock.objects.filter(is_active=True)
    return render(request, 'admin/security/account_lock_list.html', {'locks': locks})

@login_required
@require_POST
def unlock_account_view(request, user_id):
    """Разблокировать аккаунт"""
    if unlock_account(user):
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
```

### 5. Настройки Django

**Файл:** `config/settings/base.py`

```python
AUTHENTICATION_BACKENDS = [
    'apps.core.auth_backends.SecureAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

## Как это работает

### 1. Процесс блокировки

1. **Попытка входа** → проверка учетных данных
2. **Неверный пароль** → запись неудачной попытки
3. **3 попытки за 15 минут** → автоматическая блокировка
4. **Блокировка на 24 часа** → невозможно войти
5. **Автоматическая разблокировка** через 24 часа

### 2. Административное управление

1. **Дашборд безопасности** → статистика угроз
2. **Список блокировок** → все активные блокировки
3. **Детальная информация** → история попыток
4. **Разблокировка** → ручное снятие блокировки

### 3. Логирование и мониторинг

- **Все попытки** записываются с IP и User Agent
- **Блокировки** логируются с причиной
- **Успешные входы** очищают историю неудачных попыток
- **Автоматическая очистка** старых записей

## Преимущества

### 🔒 **Безопасность**
- **Защита от брутфорса** - автоматическая блокировка
- **Мониторинг IP** - отслеживание подозрительных адресов
- **Временные интервалы** - защита от быстрых атак

### 🛡️ **Контроль**
- **Полный контроль** над блокировками
- **Гибкая настройка** параметров безопасности
- **История действий** для анализа

### 📊 **Мониторинг**
- **Статистика атак** в реальном времени
- **Топ IP адресов** атакующих
- **Графики** активности угроз

## Использование

### Проверка блокировки в коде
```python
from apps.core.auth_backends import is_account_locked

if is_account_locked(user):
    # Аккаунт заблокирован
    pass
```

### Разблокировка аккаунта
```python
from apps.core.auth_backends import unlock_account

if unlock_account(user):
    # Аккаунт разблокирован
    pass
```

### Проверка количества попыток
```python
from apps.core.auth_backends import get_failed_attempts_count

attempts = get_failed_attempts_count(username)
if attempts >= 3:
    # Близко к блокировке
    pass
```

## Настройка параметров

### Изменение количества попыток
```python
# В apps/core/auth_backends.py
class SecureAuthenticationBackend(ModelBackend):
    MAX_FAILED_ATTEMPTS = 5  # Вместо 3
```

### Изменение длительности блокировки
```python
# В apps/core/models_security.py
def is_expired(self):
    return self.locked_at < timezone.now() - timedelta(hours=48)  # 48 часов
```

## URL админки

- `/security/dashboard/` - Дашборд безопасности
- `/security/locks/` - Список блокировок
- `/security/locks/<id>/` - Детали блокировки
- `/security/attempts/` - Неудачные попытки
- `/security/unlock/<id>/` - Разблокировка (POST)

## Итог

Система обеспечивает надежную защиту от подбора паролей с удобным административным интерфейсом для управления блокировками и мониторинга угроз безопасности.
