from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('ai-analyze/', views.ai_analyze_dashboard, name='ai_analyze'),
]
