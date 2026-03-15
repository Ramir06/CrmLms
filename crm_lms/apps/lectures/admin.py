from django.contrib import admin
from .models import Section, Material


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_visible']
    list_filter = ['course', 'is_visible']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'type', 'order', 'is_visible']
    list_filter = ['type', 'is_visible']
