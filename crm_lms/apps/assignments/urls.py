from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    path('courses/<int:course_id>/assignments/', views.assignments_matrix, name='matrix'),
    path('courses/<int:course_id>/assignments/create/', views.assignment_create, name='create'),
    path('submissions/<int:submission_id>/', views.submission_review, name='submission_review'),
    path('submissions/<int:submission_id>/grade/', views.grade_submission_ajax, name='grade_ajax'),
]
