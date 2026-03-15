from django.contrib import admin
from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'lesson_date', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'type', 'course']
    date_hierarchy = 'lesson_date'
