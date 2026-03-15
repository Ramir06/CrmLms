from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='list'),
    path('archive/', views.course_archive, name='archive'),
    path('create/', views.course_create, name='create'),
    path('<int:pk>/', views.course_detail, name='detail'),
    path('<int:pk>/edit/', views.course_edit, name='edit'),
    path('<int:pk>/delete/', views.course_delete, name='delete'),
    path('<int:pk>/add-student/', views.course_add_student, name='add_student'),
    path('enrollment/<int:pk>/remove/', views.remove_student, name='remove_student'),
    path('student-drawer/<int:pk>/', views.student_drawer, name='student_drawer'),
]
