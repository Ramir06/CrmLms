from django.contrib import admin
from .models import SystemSetting, FooterContent, FooterNavigationLink, SectionOrder
from ckeditor.widgets import CKEditorWidget


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'is_public', 'updated_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def value_preview(self, obj):
        if obj.key == 'footer_password':
            return '•' * 8  # Hide password
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Значение'


@admin.register(FooterContent)
class FooterContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    formfield_overrides = {
        'description': {'widget': CKEditorWidget()},
        'public_offer': {'widget': CKEditorWidget()},
    }
    
    fieldsets = (
        (None, {
            'fields': ('title', 'is_active')
        }),
        ('Контент', {
            'fields': ('description', 'public_offer', 'contact_info', 'copyright_text')
        }),
        ('Ссылки', {
            'fields': ('social_links', 'additional_links'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FooterNavigationLink)
class FooterNavigationLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'order', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'title')
    
    formfield_overrides = {
        'content': {'widget': CKEditorWidget()},
    }
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'is_active', 'order')
        }),
        ('Содержимое', {
            'fields': ('content',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SectionOrder)
class SectionOrderAdmin(admin.ModelAdmin):
    list_display = ('course', 'section', 'order')
    list_filter = ('course',)
    search_fields = ('course__title', 'section__title')
    list_editable = ('order',)
    ordering = ('course', 'order')
