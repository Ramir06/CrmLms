from django.contrib import admin
from .models import StudentRating


@admin.register(StudentRating)
class StudentRatingAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'total_score', 'rank']
    list_filter = ['course']
