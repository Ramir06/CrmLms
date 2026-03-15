from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.news_list_admin, name='admin_list'),
    path('create/', views.news_create, name='create'),
    path('<int:pk>/edit/', views.news_edit, name='edit'),
    path('<int:pk>/delete/', views.news_delete, name='delete'),
    path('<int:pk>/toggle/', views.news_toggle_publish, name='toggle'),
    path('mentor/', views.news_list_mentor, name='mentor_list'),
    path('mentor/<int:pk>/', views.news_detail_mentor, name='mentor_detail'),
]
