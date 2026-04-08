from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_dashboard, name='dashboard'),
    path('schedule/', views.student_schedule, name='schedule'),
    path('profile/', views.student_profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/settings/', views.settings_update, name='settings_update'),
    path('profile/password/', views.password_change, name='password_change'),
    path('profile/avatar/', views.avatar_upload, name='avatar_upload'),
    path('profile/two-factor/', views.two_factor_toggle, name='two_factor_toggle'),
    path('notifications/', views.student_notifications, name='notifications'),
    path('news/', views.news_list_student, name='news_list'),
    path('news/<int:pk>/', views.news_detail_student, name='news_detail'),
    path('payments/', views.student_payments, name='payments'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/materials/<int:material_id>/', views.material_detail, name='material_detail'),
    path('courses/<int:course_id>/materials/<int:material_id>/ajax/', views.material_detail_ajax, name='material_detail_ajax'),
    path('courses/<int:course_id>/attendance/', views.student_attendance, name='attendance'),
    path('courses/<int:course_id>/grades/', views.student_grades, name='grades'),
    path('courses/<int:course_id>/assignments/', views.student_assignments, name='assignments'),
    path('courses/<int:course_id>/assignments/<int:assignment_id>/ajax/', views.student_assignment_detail_ajax, name='assignment_detail_ajax'),
    path('courses/<int:course_id>/assignments/<int:assignment_id>/submit/', views.student_assignment_submit, name='assignment_submit'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/', views.student_lesson_detail, name='lesson_detail'),
    path('courses/<int:course_id>/lessons/<int:lesson_id>/ajax/', views.student_lesson_detail_ajax, name='lesson_detail_ajax'),
    path('courses/<int:course_id>/quizzes/', views.student_quizzes, name='quizzes'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/start/', views.student_quiz_start, name='quiz_start'),
    path('logout/', views.student_logout, name='logout'),
]
