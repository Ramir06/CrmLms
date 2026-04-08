from django.contrib import admin
from django.utils.html import format_html
from .models import MentorProfile


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'salary_type', 'is_active', 'hired_at']
    list_filter = ['salary_type', 'is_active']
    search_fields = ['user__full_name', 'user__email', 'specialization']
    readonly_fields = ['kpi', 'kpi_status', 'kpi_updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'short_name', 'specialization', 'bio')
        }),
        ('Зарплата', {
            'fields': ('salary_type', 'fixed_salary', 'percent_salary')
        }),
        ('KPI Метрики', {
            'fields': ('kpi', 'kpi_status', 'kpi_updated_at'),
            'classes': ('collapse',)
        }),
        ('Статус', {
            'fields': ('is_active', 'hired_at')
        })
    )
    
    actions = ['update_kpi_action']
    
    def update_kpi_action(self, request, queryset):
        """Действие для обновления KPI выбранных менторов"""
        updated = 0
        for mentor in queryset:
            try:
                from .kpi_utils import update_mentor_kpi
                result = update_mentor_kpi(mentor.user.id)
                if result:
                    updated += 1
            except Exception:
                continue
        
        self.message_user(request, f'KPI обновлён для {updated} менторов.')
    update_kpi_action.short_description = 'Обновить KPI для выбранных'
