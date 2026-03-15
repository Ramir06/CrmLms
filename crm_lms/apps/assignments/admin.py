from django.contrib import admin
from .models import Assignment, AssignmentSubmission, AssignmentGrade


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'max_score', 'due_date', 'is_visible']
    list_filter = ['course', 'is_required']


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'submitted_at']
    list_filter = ['status']


@admin.register(AssignmentGrade)
class AssignmentGradeAdmin(admin.ModelAdmin):
    list_display = ['submission', 'score', 'checked_by', 'checked_at']
