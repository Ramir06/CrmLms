from django.urls import path
from . import views
from . import views_substitute

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
    
    # KPI API endpoints
    path('api/<int:mentor_id>/kpi/', views.mentor_kpi_api, name='mentor_kpi_api'),
    path('api/<int:mentor_id>/kpi/update/', views.update_mentor_kpi_api, name='update_mentor_kpi_api'),
    path('api/kpi/', views.mentors_kpi_list, name='mentors_kpi_list'),
    path('api/my-kpi/', views.my_kpi, name='my_kpi'),
    
    # Substitute endpoints
    path('substitute/', views_substitute.substitute_courses_view, name='substitute_courses'),
    path('substitute/<int:course_id>/', views_substitute.substitute_course_detail_view, name='substitute_course_detail'),
]
