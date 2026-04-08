from django.contrib import admin
from .models import (
    CoinWallet, CoinTransaction, CoinWithdrawalSetting,
    CoinWithdrawalRequest, CoinScale, CoinBatch, CoinBatchItem
)


@admin.register(CoinWallet)
class CoinWalletAdmin(admin.ModelAdmin):
    list_display = ['student', 'balance', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['student__full_name']
    readonly_fields = ['updated_at']


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'wallet', 'amount', 'transaction_type', 'description',
        'created_by', 'created_at', 'is_cancelled'
    ]
    list_filter = ['transaction_type', 'is_cancelled', 'created_at']
    search_fields = [
        'wallet__student__full_name', 'description',
        'created_by__full_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['wallet', 'created_by', 'course', 'mentor', 'withdrawal_request', 'batch']


@admin.register(CoinWithdrawalSetting)
class CoinWithdrawalSettingAdmin(admin.ModelAdmin):
    list_display = ['is_open', 'next_open_at', 'updated_by', 'updated_at']
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        return False  # Только одна запись
    
    def has_delete_permission(self, request, obj=None):
        return False  # Нельзя удалять


@admin.register(CoinWithdrawalRequest)
class CoinWithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'amount', 'payout_method', 'phone_number',
        'status', 'created_at', 'reviewed_by'
    ]
    list_filter = ['status', 'payout_method', 'created_at']
    search_fields = ['student__full_name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['student', 'reviewed_by']


@admin.register(CoinScale)
class CoinScaleAdmin(admin.ModelAdmin):
    list_display = ['title', 'value', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'title']


@admin.register(CoinBatch)
class CoinBatchAdmin(admin.ModelAdmin):
    list_display = ['course', 'mentor', 'lesson_date', 'created_at']
    list_filter = ['lesson_date', 'created_at']
    search_fields = ['course__title', 'mentor__full_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['course', 'mentor']


@admin.register(CoinBatchItem)
class CoinBatchItemAdmin(admin.ModelAdmin):
    list_display = ['batch', 'student', 'scale', 'amount', 'description']
    list_filter = ['scale', 'created_at']
    search_fields = ['student__full_name', 'scale__title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['batch', 'student', 'scale']
