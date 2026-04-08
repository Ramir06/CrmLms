"""
Custom Exception Handlers for REST API
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError
import traceback

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для скрытия внутренних ошибок
    """
    # Вызываем стандартный обработчик DRF
    response = exception_handler(exc, context)
    
    # Если DRF не обработал исключение, создаем свой ответ
    if response is None:
        if isinstance(exc, Http404):
            error_data = {
                'error': 'Resource not found',
                'code': 'not_found',
                'status': 'error'
            }
            return Response(error_data, status=status.HTTP_404_NOT_FOUND)
        
        elif isinstance(exc, PermissionDenied):
            error_data = {
                'error': 'Access denied',
                'code': 'permission_denied',
                'status': 'error'
            }
            return Response(error_data, status=status.HTTP_403_FORBIDDEN)
        
        elif isinstance(exc, ValidationError):
            error_data = {
                'error': 'Validation failed',
                'code': 'validation_error',
                'details': str(exc),
                'status': 'error'
            }
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
        
        # Все остальные ошибки - 500, но без деталей
        logger.error(f"Unhandled API error: {exc}", exc_info=True)
        
        error_data = {
            'error': 'Internal server error',
            'code': 'server_error',
            'status': 'error',
            'request_id': getattr(context.get('request'), 'id', 'unknown')
        }
        
        return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Улучшаем стандартные ответы DRF
    if hasattr(exc, 'detail'):
        # Структурируем ошибки валидации
        if isinstance(exc.detail, dict):
            formatted_errors = {}
            for field, errors in exc.detail.items():
                if isinstance(errors, list):
                    formatted_errors[field] = errors
                elif isinstance(errors, str):
                    formatted_errors[field] = [errors]
                else:
                    formatted_errors[field] = [str(errors)]
            
            response.data = {
                'error': 'Validation failed',
                'code': 'validation_error',
                'details': formatted_errors,
                'status': 'error'
            }
        
        elif isinstance(exc.detail, list):
            response.data = {
                'error': 'Validation failed',
                'code': 'validation_error',
                'details': exc.detail,
                'status': 'error'
            }
        
        else:
            response.data = {
                'error': str(exc.detail),
                'code': 'api_error',
                'status': 'error'
            }
    
    # Добавляем request_id для отладки
    if hasattr(response, 'data') and isinstance(response.data, dict):
        request = context.get('request')
        if request:
            response.data['request_id'] = getattr(request, 'id', 'unknown')
    
    return response


class APIError(Exception):
    """Базовый класс для API ошибок"""
    
    def __init__(self, message, code=None, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code or 'api_error'
        self.status_code = status_code
        super().__init__(message)


class ValidationError(APIError):
    """Ошибка валидации"""
    
    def __init__(self, message, field=None):
        code = f'validation_error_{field}' if field else 'validation_error'
        super().__init__(message, code, status.HTTP_400_BAD_REQUEST)
        self.field = field


class AuthenticationError(APIError):
    """Ошибка аутентификации"""
    
    def __init__(self, message='Authentication failed'):
        super().__init__(message, 'authentication_error', status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(APIError):
    """Ошибка авторизации"""
    
    def __init__(self, message='Access denied'):
        super().__init__(message, 'authorization_error', status.HTTP_403_FORBIDDEN)


class NotFoundError(APIError):
    """Ресурс не найден"""
    
    def __init__(self, message='Resource not found'):
        super().__init__(message, 'not_found', status.HTTP_404_NOT_FOUND)


class RateLimitError(APIError):
    """Превышен лимит запросов"""
    
    def __init__(self, message='Rate limit exceeded', retry_after=60):
        super().__init__(message, 'rate_limit_exceeded', status.HTTP_429_TOO_MANY_REQUESTS)
        self.retry_after = retry_after


class ServerError(APIError):
    """Внутренняя ошибка сервера"""
    
    def __init__(self, message='Internal server error'):
        super().__init__(message, 'server_error', status.HTTP_500_INTERNAL_SERVER_ERROR)
