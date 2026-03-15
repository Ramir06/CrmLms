from django.urls import path
from . import views

app_name = 'debts'

urlpatterns = [
    path('', views.debt_list, name='list'),
    path('export/', views.debt_export, name='export'),
]
