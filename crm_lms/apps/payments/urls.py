from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('create/', views.payment_create, name='create'),
    path('<int:pk>/delete/', views.payment_delete, name='delete'),
    path('export/', views.payment_export, name='export'),
]
