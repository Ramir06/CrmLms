from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.lead_kanban, name='kanban'),
    path('create/', views.lead_create, name='create'),
    path('<int:pk>/', views.lead_detail, name='detail'),
    path('<int:pk>/move/', views.lead_move, name='move'),
    path('archive/', views.lead_archive, name='archive'),
]
