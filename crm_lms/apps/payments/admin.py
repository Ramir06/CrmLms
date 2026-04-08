from django.contrib import admin
from .models import Payment, OrganizationReceipt


@admin.register(OrganizationReceipt)
class OrganizationReceiptAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'organization_type', 'inn', 'tax_per_receipt', 'is_active']
    list_filter = ['organization_type', 'is_active']
    search_fields = ['organization_name', 'inn']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'amount', 'payment_method', 'paid_at', 'generate_receipt', 'created_by']
    list_filter = ['payment_method', 'course', 'generate_receipt']
    search_fields = ['student__full_name']
    date_hierarchy = 'paid_at'
