from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'attendance_status', 'mark_time']
    list_filter = ['attendance_status']
