from django.contrib import admin
from .models import SalaryAccrual


@admin.register(SalaryAccrual)
class SalaryAccrualAdmin(admin.ModelAdmin):
    list_display = ['mentor', 'course', 'month', 'amount', 'paid_status']
    list_filter = ['paid_status', 'mentor']
