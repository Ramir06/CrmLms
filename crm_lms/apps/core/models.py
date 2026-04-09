from django.db import models
from django.conf import settings
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrganizationQuerySet(models.QuerySet):
    """QuerySet с фильтрацией по организации."""
    
    def for_organization(self, organization):
        """Фильтрует данные по организации."""
        if organization is None:
            return self.none()
        return self.filter(organization=organization)
    
    def for_current_user(self, user):
        """Filter data by current user's organization. Admins see all organizations."""
        # Admins see all organizations
        if user.is_superuser:
            return self.all()
        
        try:
            from apps.organizations.models import UserCurrentOrganization
            current_org = UserCurrentOrganization.objects.filter(user=user).first()
            organization = current_org.organization if current_org else None
        except:
            organization = None
        return self.for_organization(organization)


class OrganizationManager(models.Manager):
    """Manager с фильтрацией по организации."""
    
    def get_queryset(self):
        return OrganizationQuerySet(self.model, using=self._db)
    
    def for_organization(self, organization):
        return self.get_queryset().for_organization(organization)
    
    def for_current_user(self, user):
        return self.get_queryset().for_current_user(user)


class OrganizationMixin(models.Model):
    """Mixin для добавления организации к моделям."""
    organization = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.CASCADE, 
        verbose_name="Организация",
        null=True,
        blank=True
    )
    
    objects = OrganizationManager()
    all_objects = models.Manager()  # Для доступа ко всем данным без фильтрации
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Автоматически устанавливаем организацию при сохранении
        if not hasattr(self, 'organization') or not self.organization_id:
            try:
                from apps.organizations.models import UserCurrentOrganization
                # Пытаемся получить организацию из контекста
                if hasattr(self, '_current_user'):
                    current_org = UserCurrentOrganization.objects.filter(user=self._current_user).first()
                    self.organization = current_org.organization if current_org else None
            except:
                pass
        super().save(*args, **kwargs)


class ActionHistory(TimeStampedModel, OrganizationMixin):
    """Модель для логирования действий пользователей"""
    
    ACTION_TYPES = [
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('view', 'Просмотр'),
        ('export', 'Экспорт'),
        ('import', 'Импорт'),
        ('other', 'Другое'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь',
        related_name='actions'
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        default='other',
        verbose_name='Тип действия'
    )
    action = models.CharField(
        max_length=255,
        verbose_name='Действие'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP-адрес'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    object_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Тип объекта'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='ID объекта'
    )
    object_repr = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Представление объекта'
    )
    
    class Meta:
        verbose_name = 'История действий'
        verbose_name_plural = 'История действий'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['organization', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.user} - {self.action} ({self.created_at})'
    
    @classmethod
    def log_action(cls, user, action, description='', action_type='other', 
                   ip_address=None, user_agent='', obj=None, organization=None):
        """Метод для логирования действия"""
        object_type = ''
        object_id = None
        object_repr = ''
        
        if obj:
            object_type = obj.__class__.__name__
            object_id = obj.id
            object_repr = str(obj)[:255]
        
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            action_type=action_type,
            ip_address=ip_address,
            user_agent=user_agent,
            object_type=object_type,
            object_id=object_id,
            object_repr=object_repr,
            organization=organization
        )
