from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_dashboard, name='dashboard'),
    path('transactions/', views.transaction_list, name='list'),
    path('transactions/create/', views.transaction_create, name='create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='delete'),
    path('accounts/', views.account_list, name='accounts'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('categories/', views.category_list, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('export/', views.finance_export, name='export'),
    path('api/stats/', views.finance_stats_api, name='stats_api'),
]
