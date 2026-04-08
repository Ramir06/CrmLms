from django.urls import path
from . import views

app_name = 'salaries'

urlpatterns = [
    path('', views.salary_list, name='list'),
    path('create/', views.salary_create, name='create'),
    path('<int:pk>/edit/', views.salary_edit, name='edit'),
    path('<int:pk>/details/', views.salary_details, name='details'),
    path('auto-create/', views.salary_auto_create, name='auto_create'),
    path('auto-calculate/', views.salary_auto_calculate, name='auto_calculate'),
    path('export/', views.salary_export, name='export'),
    path('mentor/', views.mentor_salary_view, name='mentor_view'),
    path('<int:salary_id>/mark-paid/', views.mark_salary_paid, name='mark_paid'),
]
