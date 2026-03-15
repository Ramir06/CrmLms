from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.admin_reports, name='admin_reports'),
    path('courses/<int:course_id>/smart-report/', views.smart_report, name='smart_report'),
]
