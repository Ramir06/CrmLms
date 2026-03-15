from django.urls import path
from . import views

app_name = 'lectures'

urlpatterns = [
    path('courses/<int:course_id>/lectures/', views.lectures_index, name='index'),
    path('courses/<int:course_id>/lectures/section/create/', views.section_create, name='section_create'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/edit/', views.section_edit, name='section_edit'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/delete/', views.section_delete, name='section_delete'),
    path('courses/<int:course_id>/lectures/material/create/', views.material_create, name='material_create'),
    path('courses/<int:course_id>/lectures/material/<int:material_id>/', views.material_detail, name='material_detail'),
    path('courses/<int:course_id>/lectures/material/<int:material_id>/delete/', views.material_delete, name='material_delete'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/add-material/', views.material_create_ajax, name='material_create_ajax'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/add-assignment/', views.assignment_create_in_section, name='assignment_create_in_section'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/add-quiz/', views.quiz_create_in_section, name='quiz_create_in_section'),
    path('courses/<int:course_id>/lectures/toggle-visibility/', views.toggle_visibility, name='toggle_visibility'),
    path('courses/<int:course_id>/lectures/assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('courses/<int:course_id>/lectures/copy-course/', views.copy_course, name='copy_course'),
    path('courses/<int:course_id>/students/', views.course_students_list, name='students'),
]
