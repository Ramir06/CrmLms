from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index_redirect, name='index'),
    path('action-history/', views.ActionHistoryListView.as_view(), name='action_history'),
    path('action-history/export/', views.action_history_export, name='action_history_export'),
]
