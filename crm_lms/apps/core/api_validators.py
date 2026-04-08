"""
API Validators and Serializers Security
"""
import re
from django.core.exceptions import ValidationError
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _


class SecurityValidator:
    """Валидаторы безопасности для API данных"""
    
    @staticmethod
    def validate_email(value):
        """Валидация email с защитой от инъекций"""
        if not value:
            return value
            
        # Базовая проверка формата
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError(_('Invalid email format'))
        
        # Проверка на опасные символы
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        if any(char in value for char in dangerous_chars):
            raise ValidationError(_('Email contains invalid characters'))
        
        # Ограничение длины
        if len(value) > 254:
            raise ValidationError(_('Email too long'))
        
        return value.lower().strip()
    
    @staticmethod
    def validate_username(value):
        """Валидация имени пользователя"""
        if not value:
            return value
        
        # Только буквы, цифры, подчеркивания, дефисы
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError(_('Username can only contain letters, numbers, underscores and hyphens'))
        
        # Ограничение длины
        if len(value) < 3 or len(value) > 50:
            raise ValidationError(_('Username must be between 3 and 50 characters'))
        
        return value.strip()
    
    @staticmethod
    def validate_phone(value):
        """Валидация телефона"""
        if not value:
            return value
        
        # Удаляем все кроме цифр
        phone_digits = re.sub(r'[^\d]', '', value)
        
        # Проверяем длину (10-15 цифр)
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            raise ValidationError(_('Invalid phone number format'))
        
        return phone_digits
    
    @staticmethod
    def validate_text_field(value, max_length=1000, allow_empty=True):
        """Валидация текстовых полей"""
        if not value:
            if not allow_empty:
                raise ValidationError(_('This field cannot be empty'))
            return value
        
        # Ограничение длины
        if len(value) > max_length:
            raise ValidationError(_(f'Text too long (max {max_length} characters)'))
        
        # Проверка на XSS
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(_('Text contains potentially dangerous content'))
        
        return value.strip()
    
    @staticmethod
    def validate_url(value):
        """Валидация URL"""
        if not value:
            return value
        
        url_pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        if not re.match(url_pattern, value):
            raise ValidationError(_('Invalid URL format'))
        
        # Ограничение длины
        if len(value) > 2048:
            raise ValidationError(_('URL too long'))
        
        return value


class SecureSerializer(serializers.Serializer):
    """Базовый сериализатор с защитой"""
    
    def validate(self, attrs):
        """Глобальная валидация данных"""
        # Проверка на пустые данные
        if not attrs:
            raise serializers.ValidationError({'non_field_errors': ['Data cannot be empty']})
        
        # Логирование попыток валидации
        request = self.context.get('request')
        if request:
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                import logging
                logger = logging.getLogger('api_validation')
                logger.info(f'Validation attempt by user {user.id} for {self.__class__.__name__}')
        
        return super().validate(attrs)


class SecureCharField(serializers.CharField):
    """Безопасное CharField с валидацией"""
    
    def __init__(self, **kwargs):
        self.max_length = kwargs.get('max_length', 255)
        self.allow_empty = kwargs.pop('allow_empty', True)
        self.strip_whitespace = kwargs.pop('strip_whitespace', True)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        if data is None:
            return data
        
        if isinstance(data, str):
            # Обрезаем пробелы
            if self.strip_whitespace:
                data = data.strip()
            
            # Валидация безопасности
            data = SecurityValidator.validate_text_field(
                data, 
                max_length=self.max_length,
                allow_empty=self.allow_empty
            )
        
        return super().to_internal_value(data)


class SecureEmailField(serializers.EmailField):
    """Безопасное EmailField"""
    
    def to_internal_value(self, data):
        if data is None:
            return data
        
        if isinstance(data, str):
            data = SecurityValidator.validate_email(data)
        
        return super().to_internal_value(data)


class SecureIntegerField(serializers.IntegerField):
    """Безопасное IntegerField с ограничениями"""
    
    def __init__(self, **kwargs):
        self.min_value = kwargs.get('min_value', 0)
        self.max_value = kwargs.get('max_value', 2147483647)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        
        # Дополнительные ограничения
        if value < self.min_value or value > self.max_value:
            raise serializers.ValidationError(
                f'Value must be between {self.min_value} and {self.max_value}'
            )
        
        return value


class SecureDateTimeField(serializers.DateTimeField):
    """Безопасное DateTimeField"""
    
    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            raise serializers.ValidationError(
                'Invalid datetime format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)'
            )


class SecureListField(serializers.ListField):
    """Безопасное ListField с ограничениями"""
    
    def __init__(self, **kwargs):
        self.max_items = kwargs.pop('max_items', 100)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError('Expected a list of items')
        
        if len(data) > self.max_items:
            raise serializers.ValidationError(f'Too many items (max {self.max_items})')
        
        return super().to_internal_value(data)


# Пример безопасного сериализатора для пользователя
class SecureUserSerializer(SecureSerializer):
    """Пример безопасного сериализатора для пользовательских данных"""
    
    username = SecureCharField(max_length=50, min_length=3)
    email = SecureEmailField()
    first_name = SecureCharField(max_length=100, allow_empty=False)
    last_name = SecureCharField(max_length=100, allow_empty=False)
    phone = SecureCharField(max_length=20, required=False, allow_empty=True)
    
    def validate_phone(self, value):
        if value:
            return SecurityValidator.validate_phone(value)
        return value
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        
        # Проверка уникальности email
        email = attrs.get('email')
        if email:
            from apps.accounts.models import CustomUser
            request = self.context.get('request')
            user = getattr(request, 'user', None)
            
            if user and CustomUser.objects.filter(email=email).exclude(pk=user.pk).exists():
                raise serializers.ValidationError({
                    'email': 'User with this email already exists'
                })
        
        return attrs


# Пример безопасного сериализатора для API ответов
class SecureResponseSerializer(SecureSerializer):
    """Сериализатор для стандартизации API ответов"""
    
    status = serializers.CharField(default='success')
    data = serializers.JSONField(required=False)
    message = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        validated_data['timestamp'] = timezone.now()
        return validated_data
