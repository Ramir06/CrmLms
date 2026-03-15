from django.contrib import admin
from .models import Debt


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'total_amount', 'paid_amount', 'status']
    list_filter = ['status', 'course']
