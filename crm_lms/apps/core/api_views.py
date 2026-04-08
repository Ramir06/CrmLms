"""
Secure API Views Examples
"""
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .api_settings import DDoSProtectionMixin, APIKeyPermission
from .api_validators import SecureSerializer, SecureUserSerializer
from .api_exceptions import APIError, ValidationError, NotFoundError
from apps.accounts.models import CustomUser


class SecureBaseViewSet(DDoSProtectionMixin, viewsets.ModelViewSet):
    """Базовый ViewSet с защитой"""
    
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ['-created_at']
    ordering_fields = ['created_at', 'updated_at']
    
    def get_queryset(self):
        """Базовый queryset с фильтрацией по организации"""
        queryset = super().get_queryset()
        
        # Фильтрация по текущей организации
        if hasattr(self.request.user, 'current_organization'):
            queryset = queryset.filter(organization=self.request.user.current_organization)
        
        return queryset
    
    def perform_create(self, serializer):
        """Безопасное создание с аудитом"""
        with transaction.atomic():
            # Добавляем создателя
            if hasattr(self.request.user, 'current_organization'):
                serializer.save(
                    created_by=self.request.user,
                    organization=self.request.user.current_organization
                )
            else:
                serializer.save(created_by=self.request.user)
    
    def handle_exception(self, exc):
        """Безопасная обработка исключений"""
        if isinstance(exc, APIError):
            return Response(
                {
                    'error': exc.message,
                    'code': exc.code,
                    'status': 'error',
                    'timestamp': timezone.now().isoformat()
                },
                status=exc.status_code
            )
        
        return super().handle_exception(exc)


class SecureAPIView(DDoSProtectionMixin, APIView):
    """Базовый API View с защитой"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        # Логирование API запросов
        self.log_api_request(request)
        
        return super().dispatch(request, *args, **kwargs)
    
    def log_api_request(self, request):
        """Логирование API запросов"""
        import logging
        logger = logging.getLogger('api_requests')
        
        user_info = 'anonymous' if isinstance(request.user, AnonymousUser) else f'user_{request.user.id}'
        
        logger.info(
            f'API Request: {request.method} {request.path} '
            f'by {user_info} from {self.get_client_ip(request)}'
        )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Пример безопасного ViewSet для пользователей
class UserViewSet(SecureBaseViewSet):
    """Пример безопасного ViewSet для управления пользователями"""
    
    serializer_class = SecureUserSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filterset_fields = ['is_active', 'role']
    
    def get_queryset(self):
        """Queryset с правами доступа"""
        user = self.request.user
        
        # Суперадмин видит всех
        if user.is_superuser:
            return CustomUser.objects.all()
        
        # Админ видит пользователей своей организации
        if hasattr(user, 'current_organization'):
            return CustomUser.objects.filter(
                organizations=user.current_organization
            )
        
        # Обычный пользователь видит только себя
        return CustomUser.objects.filter(pk=user.pk)
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    @throttle_classes([ScopedRateThrottle, 'burst'])
    def bulk_update(self, request):
        """Массовое обновление с защитой"""
        try:
            updates = request.data.get('updates', [])
            
            if len(updates) > 100:  # Ограничение на количество
                raise ValidationError('Too many items for bulk update (max 100)')
            
            results = []
            with transaction.atomic():
                for update_data in updates:
                    user_id = update_data.get('id')
                    if not user_id:
                        continue
                    
                    try:
                        user = self.get_queryset().get(pk=user_id)
                        serializer = self.get_serializer(user, data=update_data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            results.append({'id': user_id, 'success': True})
                        else:
                            results.append({
                                'id': user_id,
                                'success': False,
                                'errors': serializer.errors
                            })
                    except CustomUser.DoesNotExist:
                        results.append({'id': user_id, 'success': False, 'errors': 'User not found'})
            
            return Response({
                'status': 'success',
                'results': results,
                'processed': len(updates)
            })
            
        except Exception as e:
            raise APIError(f'Bulk update failed: {str(e)}')


# Пример безопасного API View
class UserProfileView(SecureAPIView):
    """Пример безопасного API для профиля пользователя"""
    
    def get(self, request):
        """Получение профиля"""
        try:
            user = request.user
            
            # Кэширование профиля
            cache_key = f'user_profile_{user.id}'
            profile_data = cache.get(cache_key)
            
            if not profile_data:
                profile_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.get_role_display(),
                    'is_active': user.is_active,
                    'last_login': user.last_login,
                }
                
                # Кэшируем на 5 минут
                cache.set(cache_key, profile_data, 300)
            
            return Response({
                'status': 'success',
                'data': profile_data
            })
            
        except Exception as e:
            raise APIError(f'Failed to get profile: {str(e)}')
    
    def put(self, request):
        """Обновление профиля"""
        try:
            serializer = SecureUserSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                
                # Очищаем кэш
                cache.delete(f'user_profile_{request.user.id}')
                
                return Response({
                    'status': 'success',
                    'data': serializer.data,
                    'message': 'Profile updated successfully'
                })
            else:
                raise ValidationError('Profile validation failed', serializer.errors)
                
        except ValidationError:
            raise
        except Exception as e:
            raise APIError(f'Failed to update profile: {str(e)}')


# Пример API с throttling
class PublicAPIListView(ListAPIView):
    """Пример публичного API с throttling"""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = SecureSerializer
    
    @throttle_classes([ScopedRateThrottle, 'anon'])
    def get(self, request):
        """Публичный список с throttling"""
        
        # Проверка rate limit
        client_ip = self.get_client_ip(request)
        cache_key = f'public_api_{client_ip}'
        
        request_count = cache.get(cache_key, 0)
        if request_count > 50:  # 50 запросов в час для анонимов
            raise ValidationError('Rate limit exceeded for anonymous users')
        
        cache.set(cache_key, request_count + 1, 3600)  # 1 час
        
        return Response({
            'status': 'success',
            'data': {
                'message': 'This is a public API endpoint',
                'timestamp': timezone.now().isoformat(),
                'rate_limit_info': {
                    'remaining': max(0, 50 - request_count),
                    'reset_time': timezone.now() + timezone.timedelta(hours=1)
                }
            }
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Пример API с API Key аутентификацией
class SecureDataView(SecureAPIView):
    """Пример API с API Key аутентификацией"""
    
    permission_classes = [APIKeyPermission]
    
    def get(self, request):
        """Получение защищенных данных"""
        try:
            # Проверка прав доступа
            if not request.user.has_perm('core.view_secure_data'):
                raise ValidationError('Insufficient permissions')
            
            data = {
                'secure_info': 'This is secure data',
                'access_level': 'high',
                'timestamp': timezone.now().isoformat()
            }
            
            return Response({
                'status': 'success',
                'data': data
            })
            
        except ValidationError:
            raise
        except Exception as e:
            raise APIError(f'Failed to access secure data: {str(e)}')


# Пример API с валидацией
class DataValidationView(SecureAPIView):
    """Пример API с продвинутой валидацией"""
    
    def post(self, request):
        """Создание данных с валидацией"""
        try:
            # Валидация входных данных
            serializer = SecureSerializer(data=request.data)
            if not serializer.is_valid():
                raise ValidationError('Invalid data format', serializer.errors)
            
            data = serializer.validated_data
            
            # Дополнительная бизнес-логика валидации
            if 'email' in data:
                from .api_validators import SecurityValidator
                SecurityValidator.validate_email(data['email'])
            
            if 'phone' in data:
                from .api_validators import SecurityValidator
                SecurityValidator.validate_phone(data['phone'])
            
            # Обработка данных
            result = {
                'processed_data': data,
                'validation_passed': True,
                'timestamp': timezone.now().isoformat()
            }
            
            return Response({
                'status': 'success',
                'data': result,
                'message': 'Data processed successfully'
            })
            
        except ValidationError:
            raise
        except Exception as e:
            raise APIError(f'Data processing failed: {str(e)}')
