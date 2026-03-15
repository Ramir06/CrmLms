from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'amount', 'payment_method', 'paid_at', 'created_by']
    list_filter = ['payment_method', 'course']
    search_fields = ['student__full_name']
    date_hierarchy = 'paid_at'
