from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_dashboard, name='dashboard'),
    path('sections/order/', views.update_section_order, name='update_section_order'),
    path('staff/create/', views.create_staff_user, name='create_staff_user'),
]
