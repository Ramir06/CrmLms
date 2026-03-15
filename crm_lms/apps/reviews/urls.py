from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('courses/<int:course_id>/reviews/', views.reviews_list, name='list'),
    path('courses/<int:course_id>/reviews/<int:lesson_id>/generate/', views.generate_feedback_link, name='generate_link'),
    path('courses/<int:course_id>/reviews/<int:lesson_id>/detail/', views.feedback_detail, name='detail'),
    path('feedback/<uuid:token>/', views.feedback_form, name='feedback_form'),
]
