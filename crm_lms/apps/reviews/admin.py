from django.contrib import admin
from .models import Review, LessonFeedbackLink, LessonFeedback


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['author', 'course', 'student', 'type', 'rating', 'created_at']
    list_filter = ['type', 'course']


@admin.register(LessonFeedbackLink)
class LessonFeedbackLinkAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'token', 'is_active', 'created_at']
    list_filter = ['is_active']


@admin.register(LessonFeedback)
class LessonFeedbackAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'mentor_rating', 'self_activity', 'mood', 'created_at']
    list_filter = ['feedback_link__lesson__course']
