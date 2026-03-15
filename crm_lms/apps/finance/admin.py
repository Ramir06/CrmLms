from django.contrib import admin
from .models import FinanceTransaction, FinanceCategory, FinanceAccount


@admin.register(FinanceCategory)
class FinanceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']


@admin.register(FinanceAccount)
class FinanceAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'balance']


@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = ['type', 'category', 'amount', 'account', 'transaction_date', 'created_by']
    list_filter = ['type', 'category']
    date_hierarchy = 'transaction_date'
