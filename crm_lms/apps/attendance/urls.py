from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('courses/<int:course_id>/attendance/', views.attendance_table, name='table'),
    path('courses/<int:course_id>/attendance/save/', views.save_attendance_bulk, name='save_bulk'),
    # Временный тестовый URL
    path('test/', views.test_view, name='test'),
    # Временный прямой URL для теста
    path('save-test/', views.test_save_view, name='save_test'),
    # Измененный URL чтобы избежать конфликтов
    path('course-attendance/<int:course_id>/save/', views.save_attendance_bulk, name='save_bulk_alt'),
]
