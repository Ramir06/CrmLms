from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['get_avatar_display', 'email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'full_name', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['avatar_seed', 'get_avatar_preview']

    def get_avatar_display(self, obj):
        """Отображение аватара в списке"""
        if obj.role == 'student':
            # Скрываем аватары студентов в списке
            return format_html('<span class="text-muted">Скрыто</span>')
        
        avatar_url = obj.get_avatar_url(size=50)
        return format_html('<img src="{}" width="30" height="30" class="rounded-circle" />', avatar_url)
    get_avatar_display.short_description = 'Аватар'

    def get_avatar_preview(self, obj):
        """Предпросмотр аватара в форме редактирования"""
        avatar_url = obj.get_avatar_url(size=100)
        has_custom = obj.has_custom_avatar()
        
        if has_custom:
            return format_html(
                '<img src="{}" width="100" height="100" class="rounded-circle" /><br>'
                '<small class="text-success">Загруженный аватар</small>',
                avatar_url
            )
        else:
            return format_html(
                '<img src="{}" width="100" height="100" class="rounded-circle" /><br>'
                '<small class="text-muted">RoboHash аватар</small>',
                avatar_url
            )
    get_avatar_preview.short_description = 'Предпросмотр аватара'

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'full_name', 'phone', 'avatar', 'get_avatar_preview')}),
        ('Настройки аватара', {'fields': ('avatar_seed',)}),
        ('Роль и права', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Настройки', {'fields': ('language', 'theme')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'full_name'),
        }),
    )
