from django.urls import path
from . import views
from . import settings_views

app_name = 'leads'

urlpatterns = [
    path('', views.lead_kanban, name='kanban'),
    path('create/', views.lead_create, name='create'),
    path('<int:pk>/', views.lead_detail, name='detail'),
    path('<int:pk>/delete/', views.lead_delete, name='delete'),
    path('<int:pk>/convert/', views.convert_lead_to_student, name='convert_to_student'),
    path('<int:pk>/move/', views.lead_move, name='move'),
    path('archive/', views.lead_archive, name='archive'),
    path('bulk-delete/', views.bulk_delete_leads, name='bulk_delete'),
    path('delete-status-leads/', views.delete_status_leads, name='delete_status_leads'),
    
    # Формы лидогенерации
    path('forms/', views.form_list, name='form_list'),
    path('forms/create/', views.form_create, name='form_create'),
    path('forms/<int:pk>/', views.form_detail, name='form_detail'),
    path('forms/<int:pk>/edit/', views.form_edit, name='form_edit'),
    path('forms/<int:pk>/add-field/', views.add_field_to_form, name='add_field_to_form'),
    path('forms/<int:pk>/remove-field/', views.remove_field_from_form, name='remove_field_from_form'),
    path('forms/<int:pk>/delete/', views.form_delete, name='form_delete'),
    path('forms/<int:pk>/toggle/', views.form_toggle, name='form_toggle'),
    path('forms/<int:pk>/leads/', views.form_leads, name='form_leads'),
    
    # Настройки лидов
    path('settings/', settings_views.settings_dashboard, name='settings_dashboard'),
    path('settings/status/', settings_views.lead_status_list, name='lead_status_list'),
    path('settings/status/create/', settings_views.lead_status_create, name='lead_status_create'),
    path('settings/status/<int:pk>/edit/', settings_views.lead_status_edit, name='lead_status_edit'),
    path('settings/status/<int:pk>/delete/', settings_views.lead_status_delete, name='lead_status_delete'),
    path('settings/status/<int:pk>/delete-with-leads/', settings_views.lead_status_delete_with_leads, name='lead_status_delete_with_leads'),
    path('settings/sources/', settings_views.lead_source_list, name='lead_source_list'),
    path('settings/sources/create/', settings_views.lead_source_create, name='lead_source_create'),
    path('settings/sources/<int:pk>/edit/', settings_views.lead_source_edit, name='lead_source_edit'),
    path('settings/sources/<int:pk>/delete/', settings_views.lead_source_delete, name='lead_source_delete'),
    path('settings/sources/<int:pk>/delete-with-leads/', settings_views.lead_source_delete_with_leads, name='lead_source_delete_with_leads'),
    
    # Новый функционал
    path('duplicates/', views.lead_duplicates, name='duplicates'),
    path('duplicates/find/', views.find_duplicates, name='find_duplicates'),
    path('duplicates/merge/', views.merge_leads, name='merge_leads'),
    path('duplicates/mark-not-duplicate/', views.mark_as_not_duplicate, name='mark_as_not_duplicate'),
    
    path('action-logs/', views.lead_action_logs, name='action_logs'),
    
    path('reports/', views.lead_reports, name='reports'),
    path('reports/export-leads/', views.export_leads_report, name='export_leads_report'),
    
    path('sales-reports/', views.sales_reports, name='sales_reports'),
    path('sales-reports/export/', views.export_sales_report, name='export_sales_report'),
]
