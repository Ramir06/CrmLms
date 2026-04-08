from django.middleware.csrf import CsrfViewMiddleware
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


class DevCsrfMiddleware(CsrfViewMiddleware):
    """Dev-only: trust any localhost origin regardless of port."""

    def _origin_verified(self, request):
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin.startswith('http://127.0.0.1:') or origin.startswith('http://localhost:'):
            return True
        return super()._origin_verified(request)


class OrganizationMiddleware:
    """Middleware для автоматического добавления текущей организации в request."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Добавляем текущую организацию в request для использования в views
            try:
                from .mixins import get_current_organization
                request.current_organization = get_current_organization(request.user)
            except:
                request.current_organization = None
        
        response = self.get_response(request)
        return response


class RoleMiddleware:
    """Attach role flags to the request object for easy template/view access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.is_superadmin = request.user.is_superuser
            request.is_admin = request.user.is_superuser  # Упрощаем для суперадмина
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
            
            if not request.user.is_superuser:
                return HttpResponseForbidden("""
                <div style="text-align: center; margin-top: 100px; font-family: Arial, sans-serif;">
                    <h1 style="color: #dc3545;">🚫 Access Denied</h1>
                    <p style="font-size: 18px; color: #666;">
                        You don't have permission to access the admin panel.
                    </p>
                    <p style="color: #999;">
                        Only administrators can view this page.
                    </p>
                    <a href="/" style="color: #007bff; text-decoration: none;">
                        ← Back to Home
                    </a>
                </div>
                """, content_type="text/html; charset=utf-8")
        
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


logger = logging.getLogger(__name__)


class ActionLoggingMiddleware(MiddlewareMixin):
    """Middleware для автоматического логирования действий пользователей"""
    
    # URL паттерны, которые не логируем
    SKIP_URLS = [
        '/static/',
        '/media/',
        '/admin/jsi18n/',
        '/favicon.ico',
        '/api/health/',
    ]
    
    # HTTP методы, которые логируем как 'view'
    VIEW_METHODS = ['GET', 'HEAD', 'OPTIONS']
    
    # HTTP методы, которые логируем как 'update'
    UPDATE_METHODS = ['PUT', 'PATCH', 'POST']
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Обрабатываем входящий запрос"""
        # Пропускаем статические файлы и системные URL
        if any(request.path.startswith(url) for url in self.SKIP_URLS):
            return None
        
        # Сохраняем информацию о запросе для использования в process_response
        request._action_logging_info = {
            'path': request.path,
            'method': request.method,
            'user': getattr(request, 'user', None),
        }
        
        return None
    
    def process_response(self, request, response):
        """Обрабатываем ответ и логируем действие"""
        # Получаем сохраненную информацию о запросе
        info = getattr(request, '_action_logging_info', None)
        
        if not info:
            return response
        
        # Логируем только успешные запросы (статус 2xx, 3xx)
        if response.status_code >= 400:
            return response
        
        user = info['user']
        
        # Логируем только действия аутентифицированных пользователей
        if not user or not user.is_authenticated:
            return response
        
        # Определяем тип действия
        method = info['method']
        if method in self.VIEW_METHODS:
            action_type = 'view'
        elif method in self.UPDATE_METHODS:
            action_type = 'update'
        else:
            action_type = 'other'
        
        # Пропускаем логирование некоторых view-запросов к часто посещаемым страницам
        if action_type == 'view' and self._should_skip_view_logging(request.path):
            return response
        
        # Получаем IP адрес и User Agent
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Получаем организацию пользователя
        organization = self._get_user_organization(user)
        
        # Формируем описание действия
        action, description = self._get_action_description(request, action_type)
        
        try:
            from .models import ActionHistory
            ActionHistory.log_action(
                user=user,
                action=action,
                description=description,
                action_type=action_type,
                ip_address=ip_address,
                user_agent=user_agent,
                organization=organization
            )
        except Exception as e:
            logger.error(f"Error logging action: {e}")
        
        return response
    
    def _should_skip_view_logging(self, path):
        """Определяет, нужно ли пропустить логирование view-запросов"""
        skip_paths = [
            '/dashboard/',
            '/profile/',
            '/notifications/',
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_user_organization(self, user):
        """Получает организацию пользователя"""
        try:
            from apps.organizations.models import UserCurrentOrganization
            current_org = UserCurrentOrganization.objects.filter(user=user).first()
            return current_org.organization if current_org else None
        except:
            return None
    
    def _get_action_description(self, request, action_type):
        """Формирует описание действия на основе URL и метода"""
        path = request.path
        method = request.method
        
        # Базовое описание
        if action_type == 'view':
            action = 'Просмотр страницы'
            description = f'Просмотр страницы: {path}'
        elif action_type == 'update':
            action = 'Выполнение действия'
            description = f'Выполнение {method} запроса к: {path}'
        else:
            action = 'Другое действие'
            description = f'Запрос {method} к: {path}'
        
        # Уточняем описание для известных путей
        if path.startswith('/admin/'):
            if action_type == 'view':
                action = 'Просмотр админ-панели'
                description = 'Просмотр административной панели'
            elif action_type == 'update':
                action = 'Действие в админ-панели'
                description = f'Изменение данных в админ-панели: {path}'
        
        return action, description


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Логирование входа пользователя в систему"""
    try:
        middleware = ActionLoggingMiddleware(None)
        ip_address = middleware._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        organization = middleware._get_user_organization(user)
        
        from .models import ActionHistory
        ActionHistory.log_action(
            user=user,
            action='Вход в систему',
            description=f'Пользователь {user.get_display_name()} вошел в систему',
            action_type='login',
            ip_address=ip_address,
            user_agent=user_agent,
            organization=organization
        )
    except Exception as e:
        logger.error(f"Error logging user login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Логирование выхода пользователя из системы"""
    try:
        middleware = ActionLoggingMiddleware(None)
        ip_address = middleware._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        organization = middleware._get_user_organization(user) if user else None
        
        from .models import ActionHistory
        ActionHistory.log_action(
            user=user,
            action='Выход из системы',
            description=f'Пользователь {user.get_display_name() if user else "Аноним"} вышел из системы',
            action_type='logout',
            ip_address=ip_address,
            user_agent=user_agent,
            organization=organization
        )
    except Exception as e:
        logger.error(f"Error logging user logout: {e}")
