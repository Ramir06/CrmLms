from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_list, name='list'),
    path('create/', views.transaction_create, name='create'),
    path('export/', views.finance_export, name='export'),
]
