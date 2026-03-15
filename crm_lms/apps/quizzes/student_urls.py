from django.urls import path
from . import views

urlpatterns = [
    path('take/<uuid:token>/', views.take_quiz, name='quiz_take'),
    path('result/<uuid:token>/', views.quiz_result, name='quiz_result'),
]
