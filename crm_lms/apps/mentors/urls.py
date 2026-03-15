from django.urls import path
from . import views

app_name = 'mentors'

urlpatterns = [
    path('', views.mentor_list, name='list'),
    path('create/', views.mentor_create, name='create'),
    path('<int:pk>/', views.mentor_detail, name='detail'),
    path('<int:pk>/block/', views.mentor_block, name='block'),
    path('<int:pk>/reset-password/', views.mentor_reset_password, name='reset_password'),
    path('export/', views.mentor_export, name='export'),
    path('2fa/', views.mentor_2fa_settings, name='2fa_settings'),
    path('2fa/enable/', views.enable_2fa, name='enable_2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    path('2fa/test/', views.test_2fa, name='test_2fa'),
]
