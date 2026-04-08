from django.urls import path
from . import views_course

app_name = 'mentors'

urlpatterns = [
    path('course/<int:course_id>/', views_course.mentor_course_detail, name='course_detail'),
    path('courses/<int:course_id>/students/', views_course.mentor_course_students, name='course_students'),
]
