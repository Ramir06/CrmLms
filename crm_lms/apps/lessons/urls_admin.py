from django.urls import path, include
from . import views_admin

app_name = 'admin_lessons'

urlpatterns = [
    path('courses/<int:course_id>/lessons/', views_admin.admin_lessons_calendar, name='calendar'),
    path('courses/<int:course_id>/lessons/create/', views_admin.admin_lesson_create, name='create'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/edit/', views_admin.admin_lesson_edit, name='edit'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/delete/', views_admin.admin_lesson_delete, name='delete'),
    path('', include('apps.lessons.urls_substitute')),
]
