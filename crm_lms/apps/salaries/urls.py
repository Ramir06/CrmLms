from django.urls import path
from . import views

app_name = 'salaries'

urlpatterns = [
    path('', views.salary_list, name='list'),
    path('create/', views.salary_create, name='create'),
    path('auto-create/', views.salary_auto_create, name='auto_create'),
    path('export/', views.salary_export, name='export'),
    path('mentor/', views.mentor_salary_view, name='mentor_view'),
]
