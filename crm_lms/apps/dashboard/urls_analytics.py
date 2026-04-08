from django.urls import path
from . import views_analytics

app_name = 'analytics'

urlpatterns = [
    path('', views_analytics.analytics_dashboard, name='dashboard'),
    path('course/<int:course_id>/students/', views_analytics.course_students_detail, name='course_students'),
]
