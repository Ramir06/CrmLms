from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('courses/<int:course_id>/quizzes/', views.quiz_list, name='list'),
    path('courses/<int:course_id>/quizzes/create/', views.quiz_create, name='create'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/', views.quiz_detail, name='detail'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/edit/', views.quiz_edit, name='edit'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/delete/', views.quiz_delete, name='delete'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/questions/add/', views.question_create, name='question_create'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/questions/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/start/', views.start_attempt, name='start_attempt'),
]
