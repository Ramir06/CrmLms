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
    path('courses/<int:course_id>/lectures/material/<int:material_id>/edit/', views.material_edit, name='material_edit'),
    path('courses/<int:course_id>/lectures/material/<int:material_id>/clear-content/', views.material_clear_content_ajax, name='material_clear_content_ajax'),
    path('courses/<int:course_id>/lectures/material/<int:material_id>/update-content/', views.material_update_content_ajax, name='material_update_content_ajax'),
    path('courses/<int:course_id>/lectures/material/<int:material_id>/delete/', views.material_delete, name='material_delete'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/add-material/', views.material_create_ajax, name='material_create_ajax'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/add-assignment/', views.assignment_create_in_section, name='assignment_create_in_section'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/add-assignment-form/', views.assignment_form_ajax, name='assignment_form_ajax'),
    path('courses/<int:course_id>/lectures/section/<int:section_id>/add-quiz/', views.quiz_create_in_section, name='quiz_create_in_section'),
    path('courses/<int:course_id>/lectures/toggle-visibility/', views.toggle_visibility, name='toggle_visibility'),
    path('courses/<int:course_id>/lectures/assignment/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('courses/<int:course_id>/lectures/copy/', views.copy_course, name='copy_course'),
    path('courses/<int:course_id>/students/', views.course_students_list, name='students'),
    path('courses/<int:course_id>/students/export/', views.export_students_list, name='export_students'),
    path('courses/<int:course_id>/students/<int:student_id>/', views.mentor_student_detail, name='student_detail'),
    
    # AJAX URLs для загрузки деталей
    path('courses/<int:course_id>/lectures/material/<int:material_id>/ajax/', views.material_detail_ajax, name='material_detail_ajax'),
    path('courses/<int:course_id>/lectures/assignment/<int:assignment_id>/ajax/', views.assignment_detail_ajax, name='assignment_detail_ajax'),
    path('courses/<int:course_id>/lectures/quiz/<int:quiz_id>/ajax/', views.quiz_detail_ajax, name='quiz_detail_ajax'),
    
    # AJAX URLs для управления блоками
    path('courses/<int:course_id>/lectures/block-<int:block_id>/duplicate/', views.block_duplicate_ajax, name='block_duplicate_ajax'),
    path('courses/<int:course_id>/lectures/block-<int:block_id>/delete/', views.block_delete_ajax, name='block_delete_ajax'),
    path('courses/<int:course_id>/lectures/reorder-blocks/', views.blocks_reorder_ajax, name='blocks_reorder_ajax'),
]
