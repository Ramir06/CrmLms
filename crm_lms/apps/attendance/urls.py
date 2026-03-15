from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('courses/<int:course_id>/attendance/', views.attendance_table, name='table'),
    path('courses/<int:course_id>/attendance/save/', views.save_attendance_bulk, name='save_bulk'),
]
