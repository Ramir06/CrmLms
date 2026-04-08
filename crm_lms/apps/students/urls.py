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
    path('<int:pk>/drawer/', views.student_drawer_info, name='drawer_info'),
    path('<int:pk>/detailed-excel-report/', views.student_detailed_excel_report, name='detailed_excel_report'),
    path('<int:pk>/add-admin-note/', views.add_admin_note, name='add_admin_note'),
    path('export/', views.student_export, name='export'),
    path('info/<int:student_id>/', views.student_info_page, name='info_page'),
]
