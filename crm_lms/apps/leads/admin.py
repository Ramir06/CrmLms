from django.contrib import admin
from .models import Lead, LeadAction


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'status', 'source', 'interested_course', 'created_at']
    list_filter = ['status', 'source', 'is_archived']
    search_fields = ['full_name', 'phone']


@admin.register(LeadAction)
class LeadActionAdmin(admin.ModelAdmin):
    list_display = ['lead', 'performed_by', 'old_status', 'new_status', 'created_at']
