from django.contrib import admin
from .models import SystemSetting, SectionOrder


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
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Значение'


@admin.register(SectionOrder)
class SectionOrderAdmin(admin.ModelAdmin):
    list_display = ('course', 'section', 'order')
    list_filter = ('course',)
    search_fields = ('course__title', 'section__title')
    list_editable = ('order',)
    ordering = ('course', 'order')
