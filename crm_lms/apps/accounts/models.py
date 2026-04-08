from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class Role(models.Model):
    """Модель для управления ролями и правами доступа"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name='Название роли')
    description = models.TextField(blank=True, verbose_name='Описание')
    permissions = models.JSONField(default=dict, verbose_name='Разрешенные действия')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def has_permission(self, permission):
        """Проверяет, есть ли у роли указанное разрешение"""
        return self.permissions.get(permission, False)


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, email=None, **extra_fields):
        if not username:
            raise ValueError('Username обязателен')
        
        # Генерируем avatar_seed если не предоставлен
        if not extra_fields.get('avatar_seed'):
            extra_fields['avatar_seed'] = f"user_{uuid.uuid4().hex[:12]}"
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')
        
        # Генерируем avatar_seed для суперпользователя
        if not extra_fields.get('avatar_seed'):
            extra_fields['avatar_seed'] = f"superadmin_{uuid.uuid4().hex[:12]}"
            
        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('superadmin', 'Супер-Администратор'),
        ('admin', 'Администратор'),
        ('mentor', 'Ментор'),
        ('staff', 'Персонал'),
        ('student', 'Студент'),
    ]

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('ky', 'Кыргызча'),
    ]

    THEME_CHOICES = [
        ('light', 'Светлая'),
        ('dark', 'Тёмная'),
    ]

    username = models.CharField(max_length=150, unique=True, verbose_name='Логин')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    full_name = models.CharField(max_length=200, blank=True, verbose_name='Полное имя')
    first_name = models.CharField(max_length=100, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Фамилия')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin', verbose_name='Роль')
    custom_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кастомная роль')
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
        ('ky', 'Кыргызча'),
    ]

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    avatar_seed = models.CharField(max_length=100, blank=True, unique=True, verbose_name='Seed для аватара')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='ru', verbose_name='Язык')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light', verbose_name='Тема')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    is_staff = models.BooleanField(default=False, verbose_name='Сотрудник')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name='Последний вход')

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return self.get_display_name()

    def get_display_name(self):
        if self.full_name:
            return self.full_name
        if self.first_name or self.last_name:
            return f'{self.first_name} {self.last_name}'.strip()
        return self.email

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def is_admin(self):
        return self.role in ('admin', 'superadmin')

    @property
    def is_mentor(self):
        return self.role == 'mentor'

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def get_role_display(self):
        """Возвращает отображаемое название роли с учетом кастомной роли"""
        if self.custom_role:
            return self.custom_role.name
        return self.get_role_display_legacy()
    
    def get_role_display_legacy(self):
        """Старый метод отображения роли для обратной совместимости"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def has_permission(self, permission):
        """
        Проверяет, есть ли у пользователя указанное разрешение
        """
        # Суперадминистратор имеет все права
        if self.is_superuser:
            return True
        
        # Если у пользователя есть кастомная роль, проверяем права через нее
        if self.custom_role and self.custom_role.permissions:
            return self.custom_role.has_permission(permission)
        
        # Иначе проверяем базовые права стандартной роли
        return permission in self.get_role_permissions()
    
    def get_role_permissions(self):
        """Возвращает права для стандартной роли"""
        role_permissions = {
            'superadmin': self._get_superadmin_permissions(),
            'admin': self._get_admin_permissions(),
            'mentor': self._get_mentor_permissions(),
            'staff': self._get_staff_permissions(),
            'student': self._get_student_permissions(),
        }
        
        return role_permissions.get(self.role, [])
    
    def _get_superadmin_permissions(self):
        """Права суперадмина"""
        return ['*']  # Все права
    
    def _get_admin_permissions(self):
        """Права администратора"""
        return [
            'view_users', 'add_users', 'edit_users',
            'view_students', 'add_students', 'edit_students', 'delete_students', 'manage_student_payments',
            'view_mentors', 'add_mentors', 'edit_mentors', 'delete_mentors',
            'view_courses', 'add_courses', 'edit_courses', 'delete_courses', 'manage_course_content',
            'view_organizations', 'edit_organizations', 'manage_organization_members',
            'view_payments', 'add_payments', 'edit_payments', 'view_reports',
            'view_calendar', 'edit_calendar', 'manage_lessons',
            'view_settings', 'edit_settings',
            'view_notifications', 'send_notifications',
            'access_admin_panel',
            # Права для работы с лидами
            'view_leads', 'add_leads', 'edit_leads', 'delete_leads', 'manage_leads'
        ]
    
    def _get_mentor_permissions(self):
        """Права ментора"""
        return [
            'view_students', 'edit_students',
            'view_courses', 'manage_course_content',
            'view_calendar', 'edit_calendar', 'manage_lessons',
            'view_settings'
        ]
    
    def _get_staff_permissions(self):
        """Права персонала"""
        return [
            'view_students',
            'view_courses',
            'view_calendar',
            'view_settings'
        ]
    
    def _get_student_permissions(self):
        """Права студента"""
        return [
            'view_courses',
            'view_calendar',
            'view_settings'
        ]
    
    @property
    def is_locked(self):
        """Проверяет, заблокирован ли аккаунт"""
        from apps.core.auth_backends import is_account_locked
        return is_account_locked(self)
    
    @property
    def lock_info(self):
        """Возвращает информацию о блокировке"""
        from apps.core.auth_backends import get_account_lock_info
        return get_account_lock_info(self)
    
    def unlock_account(self):
        """Разблокировать аккаунт (только для администраторов)"""
        from apps.core.auth_backends import unlock_account
        return unlock_account(self)
    
    def get_last_login_display(self):
        """Возвращает отформатированное время последнего входа"""
        if self.last_login_at:
            return self.last_login_at.strftime('%d.%m.%Y %H:%M')
        return 'Никогда'
    
    def save(self, *args, **kwargs):
        # При сохранении пользователя с кастомной ролью, устанавливаем is_staff=True
        if self.custom_role and not self.is_staff:
            self.is_staff = True
        
        # Для стандартных ролей admin и superadmin тоже устанавливаем is_staff
        if self.role in ['admin', 'superadmin'] and not self.is_staff:
            self.is_staff = True
        
        # При сохранении пользователя генерируем avatar_seed при необходимости
        if not self.avatar_seed:
            # Генерируем уникальный seed на основе ID и UUID
            if self.id:
                self.avatar_seed = f"user_{self.id}_{uuid.uuid4().hex[:8]}"
            else:
                self.avatar_seed = f"user_{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)
    
    def get_avatar_url(self, size=300):
        """
        Возвращает URL аватара пользователя.
        Если загружен свой аватар - возвращает его URL.
        Если нет - возвращает RoboHash URL на основе avatar_seed.
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        
        # Fallback: если avatar_seed почему-то пустой, генерируем его
        if not self.avatar_seed:
            if not self.id:
                # Если пользователя еще нет в БД, используем username
                seed = f"user_{self.username}_{uuid.uuid4().hex[:8]}"
            else:
                seed = f"user_{self.id}_{uuid.uuid4().hex[:8]}"
        else:
            seed = self.avatar_seed
        
        # Возвращаем RoboHash URL
        return f"https://robohash.org/{seed}?set=set1&size={size}x{size}"
    
    @property
    def avatar_url(self):
        """Свойство для удобного доступа к URL аватара"""
        return self.get_avatar_url()
    
    def has_custom_avatar(self):
        """Проверяет, есть ли у пользователя загруженный аватар"""
        return bool(self.avatar and hasattr(self.avatar, 'url'))
    
    def delete_avatar(self):
        """Удаляет загруженный аватар"""
        if self.avatar:
            # Удаляем файл с диска
            if hasattr(self.avatar, 'delete'):
                self.avatar.delete(save=False)
            # Очищаем поле
            self.avatar = None
            self.save()


class UserAccount(models.Model):
    """Модель для хранения мультиаккаунтов пользователя"""
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='user_accounts',
        verbose_name='Основной пользователь'
    )
    account_user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='linked_accounts',
        verbose_name='Связанный аккаунт'
    )
    name = models.CharField(max_length=100, verbose_name='Название аккаунта')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    last_used = models.DateTimeField(null=True, blank=True, verbose_name='Последнее использование')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Аккаунт пользователя'
        verbose_name_plural = 'Аккаунты пользователей'
        unique_together = ['user', 'account_user']
        ordering = ['-last_used', '-created_at']
    
    def __str__(self):
        return f"{self.user.get_display_name()} -> {self.name}"
    
    def mark_as_used(self):
        """Отметить аккаунт как использованный"""
        from django.utils import timezone
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])
