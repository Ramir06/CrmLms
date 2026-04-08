from django.contrib import admin
from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'type', 'get_user_display', 
        'email', 'created_at', 'telegram_sent'
    ]
    list_filter = ['type', 'telegram_sent', 'created_at']
    search_fields = ['title', 'description', 'email', 'user__email']
    readonly_fields = ['created_at', 'telegram_message_id']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('type', 'title', 'description')
        }),
        ('Пользователь', {
            'fields': ('user', 'email')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'telegram_sent', 'telegram_message_id'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_display(self, obj):
        return obj.get_user_display()
    get_user_display.short_description = 'Автор'
    
    list_per_page = 20
    ordering = ['-created_at']
