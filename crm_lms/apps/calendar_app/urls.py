from django.urls import path
from . import views

app_name = 'calendar_app'

urlpatterns = [
    path('admin/', views.admin_calendar, name='admin_calendar'),
    path('mentor/', views.mentor_calendar, name='mentor_calendar'),
    path('api/events/', views.calendar_events_api, name='events_api'),
    path('event/<int:pk>/drawer/', views.lesson_drawer, name='lesson_drawer'),
    path('event/<int:pk>/mark-attendance/', views.save_attendance, name='save_attendance'),
    path('create-event/', views.create_event, name='create_event'),
]
