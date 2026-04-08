# Безопасность проекта: Защита от несанкционированного доступа

## Описание

Добавлена система безопасности, которая предотвращает доступ менторов и других пользователей к административным разделам системы.

## Реализация

### 1. Обновленный RoleMiddleware

**Файл:** `apps/core/middleware.py`

```python
class RoleMiddleware:
    """Attach role flags to the request object for easy template/view access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.is_superadmin = request.user.role == 'superadmin'
            request.is_admin = request.user.role in ('admin', 'superadmin')
            request.is_mentor = request.user.role == 'mentor'
            request.is_student = request.user.role == 'student'
        else:
            request.is_superadmin = False
            request.is_admin = False
            request.is_mentor = False
            request.is_student = False
        
        # Проверка доступа к админским URL
        if self._is_admin_path(request.path):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if not request.user.role in ('admin', 'superadmin'):
                return HttpResponseForbidden("""
                <div style="text-align: center; margin-top: 100px; font-family: Arial, sans-serif;">
                    <h1 style="color: #dc3545;">🚫 Доступ запрещен</h1>
                    <p style="font-size: 18px; color: #666;">
                        У вас нет прав доступа к административной панели.
                    </p>
                    <p style="color: #999;">
                        Только администраторы могут просматривать эту страницу.
                    </p>
                    <a href="/" style="color: #007bff; text-decoration: none;">
                        ← Вернуться на главную
                    </a>
                </div>
                """, content_type="text/html")
        
        response = self.get_response(request)
        return response
    
    def _is_admin_path(self, path):
        """Проверяет, является ли путь админским"""
        admin_paths = [
            '/admin/',
            '/dashboard/admin/',
            '/courses/admin/',
            '/students/admin/',
            '/mentors/admin/',
            '/leads/admin/',
            '/attendance/admin/',
            '/assignments/admin/',
            '/finance/admin/',
            '/reports/admin/',
            '/news/admin/',
            '/notifications/admin/',
            '/settings/admin/',
        ]
        return any(path.startswith(admin_path) for admin_path in admin_paths)
```

### 2. Настройки Django

**Файл:** `config/settings/dev.py`

```python
# Add back RoleMiddleware with security features
MIDDLEWARE = [
    m for m in MIDDLEWARE 
    if m != 'apps.core.middleware.RoleMiddleware'
]

# Add RoleMiddleware back for security
MIDDLEWARE.append('apps.core.middleware.RoleMiddleware')
```

### 3. Исправление URL ошибок

**Файл:** `templates/mentor/dashboard/index.html`

Исправлены проблемы с URL:
- Добавлена проверка `course.pk` перед формированием URL
- Исправлены переменные в шаблонах замененных курсов

## Как это работает

### 1. Проверка доступа
1. **Middleware перехватывает** каждый запрос
2. **Проверяет путь** на принадлежность к админским разделам
3. **Проверяет роль** пользователя
4. **Блокирует доступ** если у пользователя нет прав

### 2. Защищенные пути
- `/admin/` - Django админка
- `/dashboard/admin/` - Админский дашборд
- `/courses/admin/` - Управление курсами
- `/students/admin/` - Управление студентами
- `/mentors/admin/` - Управление менторами
- `/leads/admin/` - Управление лидами
- `/attendance/admin/` - Управление посещаемостью
- `/assignments/admin/` - Управление заданиями
- `/finance/admin/` - Финансовые разделы
- `/reports/admin/` - Отчеты
- `/news/admin/` - Управление новостями
- `/notifications/admin/` - Управление уведомлениями
- `/settings/admin/` - Настройки системы

### 3. Результат блокировки
При попытке доступа к защищенному разделу пользователь видит:
- **Красную страницу** с сообщением "Доступ запрещен"
- **Объяснение** что только администраторы имеют доступ
- **Ссылку** для возврата на главную страницу

## Преимущества

### 1. Безопасность
- **Полная изоляция** админских функций
- **Автоматическая блокировка** несанкционированного доступа
- **Централизованная проверка** в одном месте

### 2.用户体验
- **Четкое сообщение** об отказе в доступе
- **Понятная причина** блокировки
- **Удобная навигация** обратно

### 3. Администрирование
- **Простое управление** правами доступа
- **Легкое расширение** списка защищенных путей
- **Унифицированная логика** проверки ролей

## Использование

### Проверка ролей в коде
```python
# В views
if request.is_admin:
    # Админский код
    pass

# В шаблонах
{% if request.is_admin %}
    <!-- Админский контент -->
{% endif %}
```

### Добавление новых защищенных путей
```python
def _is_admin_path(self, path):
    """Проверяет, является ли путь админским"""
    admin_paths = [
        '/admin/',
        '/dashboard/admin/',
        # Добавить новые пути сюда
        '/new/admin/path/',
    ]
    return any(path.startswith(admin_path) for admin_path in admin_paths)
```

### Кастомизация страницы блокировки
```python
return HttpResponseForbidden(custom_template, content_type="text/html")
```

## Тестирование

### 1. Тест доступа ментора
```bash
# Войти как ментор и попытаться перейти на:
http://127.0.0.1:8000/admin/
http://127.0.0.1:8000/dashboard/admin/
# Должна появиться страница "Доступ запрещен"
```

### 2. Тест доступа администратора
```bash
# Войти как администратор - те же URL должны работать
```

### 3. Тест доступа студента
```bash
# Войти как студент - должен быть заблокирован доступ
```

## Итог

Система обеспечивает надежную защиту административных функций от несанкционированного доступа, сохраняя при этом удобный интерфейс для легитимных пользователей.
