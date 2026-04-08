from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('', views.feedback_list, name='feedback_list'),
    path('<str:feedback_type>/', views.feedback_form, name='feedback_form'),
    path('success/', views.feedback_success, name='success'),
    path('quick/', views.quick_feedback, name='quick_feedback'),
]
