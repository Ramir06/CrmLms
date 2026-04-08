from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Organization(models.Model):
    """Модель организации для мультитенантности."""
    name = models.CharField(max_length=200, verbose_name="Название организации")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL идентификатор")
    code = models.CharField(max_length=10, verbose_name="Код филиала", help_text="Код в формате 0084", default='0084')
    description = models.TextField(blank=True, verbose_name="Описание")
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True, verbose_name="Логотип")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
        ordering = ['name']

    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    """Участники организации."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members', verbose_name="Организация")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    role = models.CharField(max_length=20, choices=[
        ('owner', 'Владелец'),
        ('admin', 'Администратор'),
        ('member', 'Участник'),
    ], default='member', verbose_name="Роль")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата вступления")

    class Meta:
        verbose_name = "Участник организации"
        verbose_name_plural = "Участники организаций"
        unique_together = ['organization', 'user']

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.organization.name}"


class UserCurrentOrganization(models.Model):
    """Текущая организация пользователя."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='current_organization',
        verbose_name="Пользователь"
    )
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        verbose_name="Текущая организация"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Текущая организация"
        verbose_name_plural = "Текущие организации"

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.organization.name}"


class StaffMember(models.Model):
    """Персонал с доступом к организациям"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='staff_member', verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_staff', verbose_name='Кто создал'
    )
    
    class Meta:
        verbose_name = 'Персонал'
        verbose_name_plural = 'Персонал'
    
    def __str__(self):
        return f'{self.user.get_display_name()}'
    
    @property
    def organizations(self):
        """Возвращает организации, к которым у персонала есть доступ"""
        return Organization.objects.filter(
            staff_access__staff_member=self,
            staff_access__is_active=True
        )


class StaffOrganizationAccess(models.Model):
    """Доступ персонала к организации"""
    staff_member = models.ForeignKey(
        StaffMember, on_delete=models.CASCADE,
        related_name='staff_access', verbose_name='Персонал'
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE,
        related_name='staff_access', verbose_name='Организация'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата предоставления')
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='granted_access', verbose_name='Кто предоставил'
    )
    
    class Meta:
        verbose_name = 'Доступ персонала к организации'
        verbose_name_plural = 'Доступ персонала к организациям'
        unique_together = ['staff_member', 'organization']
    
    def __str__(self):
        return f'{self.staff_member} → {self.organization}'
