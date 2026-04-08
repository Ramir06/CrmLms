from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Управление комнатами (только для админов)
    path('management/', views.room_management, name='room_management'),
    path('management/edit/<int:room_id>/', views.edit_room, name='edit_room'),
]
