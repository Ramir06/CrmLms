from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('accounts/add/', views.add_account_view, name='add_account'),
    path('accounts/manage/', views.manage_accounts_view, name='manage_accounts'),
    path('accounts/switch/<int:account_id>/', views.switch_account_view, name='switch_account'),
    path('accounts/remove/<int:account_id>/', views.remove_account_view, name='remove_account'),
    path('api/accounts/', views.api_accounts_list, name='api_accounts'),
    
    # Управление ролями
    path('roles/', views.roles_list, name='roles_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:pk>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:pk>/delete/', views.role_delete, name='role_delete'),
]
