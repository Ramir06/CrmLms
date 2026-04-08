"""
REST API Security Configuration
"""
from rest_framework import permissions
from rest_framework.throttling import ScopedRateThrottle, UserRateThrottle, AnonRateThrottle
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
import time


class SecurePageNumberPagination(PageNumberPagination):
    """Безопасная пагинация с ограничениями"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


class DDoSProtectionMixin:
    """Защита от DDoS на уровне приложения"""
    
    def dispatch(self, request, *args, **kwargs):
        # Проверка rate limit по IP
        client_ip = self.get_client_ip(request)
        cache_key = f"ddos_protection_{client_ip}"
        
        # Получаем текущий счетчик
        requests_count = cache.get(cache_key, 0)
        
        # Если превышен лимит - блокируем
        if requests_count > 1000:  # 1000 запросов в минуту
            return Response(
                {'error': 'Rate limit exceeded. Try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Увеличиваем счетчик
        cache.set(cache_key, requests_count + 1, 60)  # 1 минута
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CustomRateThrottle(ScopedRateThrottle):
    """Кастомный throttle с детализацией"""
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return f'rate_limit_{view.scope}_{ident}'
    
    def throttle_failure(self):
        wait_time = self.wait()
        
        response_data = {
            'error': 'Rate limit exceeded',
            'detail': f'Too many requests. Try again in {int(wait_time)} seconds.',
            'retry_after': int(wait_time)
        }
        
        from rest_framework.response import Response
        from rest_framework import status
        
        return Response(response_data, status=status.HTTP_429_TOO_MANY_REQUESTS)


class BurstRateThrottle(CustomRateThrottle):
    """Защита от burst атак"""
    scope = 'burst'


class SustainedRateThrottle(CustomRateThrottle):
    """Защита от продолжительных атак"""
    scope = 'sustained'


class APIKeyPermission(permissions.BasePermission):
    """Разрешение на основе API ключа"""
    
    def has_permission(self, request, view):
        # Для админских запросов не требуется API ключ
        if request.user.is_staff and request.user.is_authenticated:
            return True
            
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return False
            
        # Проверка валидности API ключа
        valid_keys = getattr(settings, 'VALID_API_KEYS', [])
        return api_key in valid_keys


class SecureIsAuthenticated(permissions.IsAuthenticated):
    """Усиленная проверка аутентификации"""
    
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        
        # Дополнительная проверка на активность пользователя
        if is_authenticated and hasattr(request.user, 'is_active'):
            return request.user.is_active
            
        return is_authenticated


# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'apps.core.api_settings.SecureIsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.core.api_settings.BurstRateThrottle',
        'apps.core.api_settings.SustainedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'burst': '100/min',      # Burst: 100 запросов в минуту
        'sustained': '1000/hour', # Sustained: 1000 запросов в час
        'anon': '20/min',         # Анонимные: 20 в минуту
        'user': '1000/min',       # Аутентифицированные: 1000 в минуту
    },
    'DEFAULT_PAGINATION_CLASS': 'apps.core.api_settings.SecurePageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'apps.core.api_exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Spectacular (API Docs) Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'CRM LMS API',
    'DESCRIPTION': 'Secure API for CRM LMS System',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
}
