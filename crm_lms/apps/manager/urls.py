from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    path('', views.dashboard_index, name='dashboard'),
    path('dashboard/', views.dashboard_index, name='index'),
    path('test/', views.test_dashboard, name='test'),
]
