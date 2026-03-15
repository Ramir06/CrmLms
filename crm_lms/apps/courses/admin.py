from django.contrib import admin
from .models import Course, CourseStudent


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'status', 'mentor', 'start_date', 'capacity']
    list_filter = ['status', 'format', 'is_archived']
    search_fields = ['title', 'subject']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(CourseStudent)
class CourseStudentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'joined_at']
    list_filter = ['status', 'course']
    search_fields = ['student__full_name', 'course__title']
