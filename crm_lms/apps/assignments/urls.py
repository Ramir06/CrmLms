from django.urls import path
from . import views
from . import views_ai_grading

app_name = 'assignments'

urlpatterns = [
    path('courses/<int:course_id>/assignments/', views.assignments_matrix, name='matrix'),
    path('courses/<int:course_id>/assignments/create/', views.assignment_create, name='create'),
    path('courses/<int:course_id>/assignments/<int:assignment_id>/solutions/', views.assignment_solutions, name='assignment_solutions'),
    path('courses/<int:course_id>/student-stats/', views.student_stats, name='student_stats'),
    path('submissions/<int:submission_id>/', views.submission_review, name='submission_review'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission_ajax, name='grade_ajax'),
    path('courses/<int:course_id>/assignments/<int:assignment_id>/students/<int:student_id>/grade/', views.create_grade_ajax, name='create_grade_ajax'),
    
    # AI-оценка
    path('ai-grading/', views_ai_grading.ai_grading_dashboard, name='ai_grading_dashboard'),
    path('ai-grade/<int:submission_id>/', views_ai_grading.ai_grade_submission, name='ai_grade_submission'),
    path('batch-ai-grade/', views_ai_grading.batch_ai_grade, name='batch_ai_grade'),
    path('ai-review/<int:submission_id>/', views_ai_grading.ai_grading_review, name='ai_grading_review'),
    path('override-ai-grade/<int:submission_id>/', views_ai_grading.override_ai_grade, name='override_ai_grade'),
    
    # Новые AI функции
    path('submissions/<int:submission_id>/ai-check/', views.ai_check_submission, name='ai_check_submission'),
    path('courses/<int:course_id>/ai-analyze/', views.ai_analyze_class, name='ai_analyze_class'),
]
