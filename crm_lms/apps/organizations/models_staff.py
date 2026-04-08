from django.db import models
from django.contrib.auth import get_user_model
from .models import Organization

User = get_user_model()


class StaffMember(models.Model):
    """Персонал с доступом к организациям"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='staff_member', verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
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
        User, on_delete=models.SET_NULL, null=True,
        related_name='granted_access', verbose_name='Кто предоставил'
    )
    
    class Meta:
        verbose_name = 'Доступ персонала к организации'
        verbose_name_plural = 'Доступ персонала к организациям'
        unique_together = ['staff_member', 'organization']
    
    def __str__(self):
        return f'{self.staff_member} → {self.organization}'
