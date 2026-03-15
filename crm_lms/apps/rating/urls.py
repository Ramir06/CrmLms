from django.urls import path
from . import views

app_name = 'rating'

urlpatterns = [
    path('courses/<int:course_id>/rating/', views.rating_table, name='table'),
]
