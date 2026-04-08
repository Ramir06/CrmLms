from django.urls import path
from . import views, api_views, views_staff, views_superadmin

app_name = 'organizations'

urlpatterns = [
    path('', views.organization_list, name='list'),
    path('create/', views.organization_create, name='create'),
    path('edit-current/', views.edit_current, name='edit_current'),
    path('superadmin/', views_superadmin.superadmin_organizations, name='superadmin_organizations'),
    path('superadmin/<int:pk>/', views_superadmin.superadmin_organization_detail, name='superadmin_organization_detail'),
    path('superadmin/<int:org_pk>/create-staff/', views_superadmin.superadmin_create_staff, name='superadmin_create_staff'),
    path('superadmin/<int:org_pk>/toggle-user/<int:pk>/', views_superadmin.superadmin_toggle_user, name='superadmin_toggle_user'),
    path('<int:pk>/', views.organization_detail, name='detail'),
    path('<int:pk>/edit/', views.organization_edit, name='edit'),
    path('<int:pk>/delete/', views.organization_delete, name='delete'),
    path('switch/<int:pk>/', views.switch_organization, name='switch'),
    path('my/', views.my_organizations, name='my_organizations'),
    
    # API endpoints
    path('api/', api_views.OrganizationsAPI.as_view(), name='api_list'),
    path('api/<int:pk>/switch/', api_views.SwitchOrganizationAPI.as_view(), name='api_switch'),
    
    # Staff management
    path('staff/', views_staff.StaffListView.as_view(), name='staff_list'),
    path('staff/create/', views_staff.staff_create, name='staff_create'),
    path('staff/<int:pk>/', views_staff.staff_detail, name='staff_detail'),
    path('staff/<int:pk>/edit-access/', views_staff.staff_edit_access, name='staff_edit_access'),
    path('staff/<int:pk>/toggle/', views_staff.staff_toggle_active, name='staff_toggle_active'),
    path('staff/<int:pk>/delete/', views_staff.staff_delete, name='staff_delete'),
]
