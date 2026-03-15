from django.contrib import admin
from .models import News


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'audience', 'is_published', 'published_at', 'created_by']
    list_filter = ['audience', 'is_published']
    search_fields = ['title']
