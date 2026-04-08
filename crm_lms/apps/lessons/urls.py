from django.urls import path, include
from . import views

app_name = 'lessons'

urlpatterns = [
    path('courses/<int:course_id>/lessons/', views.lessons_calendar, name='calendar'),
    path('courses/<int:course_id>/lessons/create/', views.lesson_create, name='create'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/edit/', views.lesson_edit, name='edit'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/delete/', views.lesson_delete, name='delete'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/mark-completed/', views.mark_lesson_completed, name='mark_completed'),
]
