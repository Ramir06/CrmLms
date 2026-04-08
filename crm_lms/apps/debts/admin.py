from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Debt


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course', 'total_amount', 'paid_amount', 
        'debt_amount', 'status', 'month_year_display', 'created_at'
    ]
    list_filter = ['status', 'course', 'debt_type', 'month', 'year']
    search_fields = ['student__full_name', 'course__title']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['mark_as_paid', 'refresh_debtors']
    
    def month_year_display(self, obj):
        return f"{obj.month:02d}.{obj.year}"
    month_year_display.short_description = 'Месяц/Год'
    
    def debt_amount(self, obj):
        amount = obj.total_amount - obj.paid_amount
        if amount > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', amount)
        return format_html('<span style="color: green;">{}</span>', amount)
    debt_amount.short_description = 'Сумма долга'
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')
        self.message_user(request, f'Отмечено как оплачено: {queryset.count()} долгов')
    mark_as_paid.short_description = 'Отметить как оплаченные'
    
    def refresh_debtors(self, request, queryset):
        """Обновить список должников"""
        created_count = Debt.objects.create_or_update_debts()
        self.message_user(request, 'Список должников обновлен')
    refresh_debtors.short_description = 'Обновить список должников'
    
    def changelist_view(self, request, extra_context=None):
        """Автоматически обновляем должников при открытии страницы"""
        try:
            Debt.objects.create_or_update_debts()
        except Exception as e:
            pass  # Игнорируем ошибки, чтобы не сломать админ-панель
        
        extra_context = extra_context or {}
        extra_context['title'] = 'Должники'
        return super().changelist_view(request, extra_context)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('student', 'course', 'status', 'debt_type')
        }),
        ('Финансовая информация', {
            'fields': ('total_amount', 'paid_amount')
        }),
        ('Период', {
            'fields': ('month', 'year')
        }),
        ('Дополнительно', {
            'fields': ('note', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
