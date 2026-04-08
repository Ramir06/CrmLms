from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_dashboard, name='dashboard'),
    path('update/', views.update_system_settings, name='update_system'),
    path('sections/order/', views.update_section_order, name='update_section_order'),
    path('staff/create/', views.create_staff_user, name='create_staff_user'),
    
    # Способы оплаты
    path('payment-methods/', views.payment_methods_list, name='payment_methods_list'),
    path('payment-methods/create/', views.payment_method_create, name='payment_method_create'),
    path('payment-methods/<int:pk>/edit/', views.payment_method_edit, name='payment_method_edit'),
    path('payment-methods/<int:pk>/delete/', views.payment_method_delete, name='payment_method_delete'),
    path('payment-methods/<int:pk>/toggle/', views.payment_method_toggle, name='payment_method_toggle'),
    
    # Управление футером
    path('footer/', views.footer_editor, name='footer_editor'),
    path('footer-navigation/', views.footer_navigation_list, name='footer_navigation_list'),
    path('footer-navigation/add/', views.footer_navigation_add, name='footer_navigation_add'),
    path('footer/check-password/', views.footer_password_check, name='footer_password_check'),
]
