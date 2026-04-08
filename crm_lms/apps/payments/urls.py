from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('create/', views.payment_create, name='create'),
    path('create/null/', views.payment_create, name='create_null'),  # Добавляем обработку /null
    path('receipt/<int:payment_id>/', views.show_payment_receipt, name='show_receipt'),
    path('<int:pk>/delete/', views.payment_delete, name='delete'),
    path('export/', views.payment_export, name='export'),
    path('api/student/<int:student_id>/courses/', views.get_student_courses, name='api_student_courses'),
    path('organization-settings/', views.organization_settings, name='organization_settings'),
]
