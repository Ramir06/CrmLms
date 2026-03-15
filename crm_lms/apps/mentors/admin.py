from django.contrib import admin
from .models import MentorProfile


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'salary_type', 'is_active', 'hired_at']
    list_filter = ['salary_type', 'is_active']
    search_fields = ['user__full_name', 'user__email', 'specialization']
