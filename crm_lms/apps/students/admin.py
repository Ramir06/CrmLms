from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'status', 'source', 'created_at']
    list_filter = ['status', 'gender', 'source']
    search_fields = ['full_name', 'phone', 'parent_name']
