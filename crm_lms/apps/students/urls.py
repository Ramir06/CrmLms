from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='list'),
    path('create/', views.student_create, name='create'),
    path('<int:pk>/', views.student_detail, name='detail'),
    path('<int:pk>/edit/', views.student_edit, name='edit'),
    path('<int:pk>/delete/', views.student_delete, name='delete'),
    path('<int:pk>/block/', views.student_block, name='block'),
    path('<int:pk>/reset-password/', views.student_reset_password, name='reset_password'),
    path('export/', views.student_export, name='export'),
]
