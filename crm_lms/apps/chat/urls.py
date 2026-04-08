from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Основные страницы чата
    path('', views.chat_room_list, name='room_list'),
    path('room/<int:room_id>/', views.chat_room, name='room'),
    
    # AJAX функции для сообщений
    path('send/<int:room_id>/', views.send_message, name='send_message'),
    path('edit/<int:message_id>/', views.edit_message, name='edit_message'),
    path('delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('pin/<int:message_id>/', views.pin_message, name='pin_message'),
    path('new-messages/<int:room_id>/', views.get_new_messages, name='get_new_messages'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
    
    # Управление комнатами (только для админов)
    path('management/', views.room_management, name='room_management'),
    path('management/edit/<int:room_id>/', views.edit_room, name='edit_room'),
]
