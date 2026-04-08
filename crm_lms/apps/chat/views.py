from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Q, Max, Count
from django.contrib import messages
import json
from datetime import timedelta

from apps.core.mixins import admin_required, mentor_required
from .models import ChatRoom, ChatMessage, ChatReadStatus, ChatAttachment
from .forms import ChatMessageForm, ChatMessageEditForm, ChatAttachmentForm, ChatRoomForm


def can_access_chat(user):
    """Проверка прав доступа к чату"""
    return user.role in ('admin', 'superadmin', 'mentor')


@login_required
def chat_room_list(request):
    """Список комнат чата"""
    if not can_access_chat(request.user):
        return redirect('dashboard')
    
    rooms = ChatRoom.objects.filter(is_active=True).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
    # Получаем или создаем статус прочтения для каждой комнаты
    for room in rooms:
        ChatReadStatus.objects.get_or_create(user=request.user, room=room)
    
    context = {
        'rooms': rooms,
        'page_title': 'Чат',
        'active_menu': 'chat',
    }
    return render(request, 'chat/room_list.html', context)


@login_required
def chat_room(request, room_id):
    """Комната чата"""
    if not can_access_chat(request.user):
        return redirect('dashboard')
    
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    
    # Получаем сообщения (не удаленные)
    messages = ChatMessage.objects.filter(
        room=room, 
        is_deleted=False
    ).select_related('author').order_by('-is_pinned', 'created_at')
    
    # Обновляем статус прочтения
    read_status, created = ChatReadStatus.objects.get_or_create(
        user=request.user, 
        room=room
    )
    if messages.exists():
        read_status.last_read_message = messages.first()
        read_status.save()
    
    # Формы
    message_form = ChatMessageForm()
    attachment_form = ChatAttachmentForm()
    
    context = {
        'room': room,
        'messages': messages,
        'message_form': message_form,
        'attachment_form': attachment_form,
        'page_title': f'Чат - {room.name}',
        'active_menu': 'chat',
    }
    return render(request, 'chat/room.html', context)


@login_required
@require_POST
def send_message(request, room_id):
    """Отправка сообщения"""
    if not can_access_chat(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    form = ChatMessageForm(request.POST)
    
    if form.is_valid():
        message = form.save(commit=False)
        message.room = room
        message.author = request.user
        message.save()
        
        # Обновляем статус прочтения для автора
        read_status, _ = ChatReadStatus.objects.get_or_create(
            user=request.user, 
            room=room
        )
        read_status.last_read_message = message
        read_status.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'author': message.author.get_display_name(),
                'author_id': message.author.id,
                'created_at': message.created_at.strftime('%H:%M'),
                'can_edit': message.can_edit,
                'can_delete': message.can_delete,
                'is_pinned': message.is_pinned,
            }
        })
    
    return JsonResponse({'error': 'Неверные данные'}, status=400)


@login_required
@require_POST
def edit_message(request, message_id):
    """Редактирование сообщения"""
    if not can_access_chat(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    message = get_object_or_404(ChatMessage, id=message_id, author=request.user)
    
    if not message.can_edit:
        return JsonResponse({'error': 'Нельзя редактировать это сообщение'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return JsonResponse({'error': 'Содержание не может быть пустым'}, status=400)
        
        message.content = new_content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        
        return JsonResponse({
            'success': True,
            'content': message.content,
            'edited_at': message.edited_at.strftime('%H:%M')
        })
        
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Неверные данные'}, status=400)


@login_required
@require_POST
def delete_message(request, message_id):
    """Удаление сообщения"""
    if not can_access_chat(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    message = get_object_or_404(ChatMessage, id=message_id)
    
    # Проверяем права: автор может удалить, админ может удалить любое
    if message.author != request.user and request.user.role not in ('admin', 'superadmin'):
        return JsonResponse({'error': 'Нельзя удалить это сообщение'}, status=403)
    
    if not message.can_delete and message.author == request.user:
        return JsonResponse({'error': 'Нельзя удалить это сообщение'}, status=403)
    
    message.is_deleted = True
    message.deleted_at = timezone.now()
    message.save()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def pin_message(request, message_id):
    """Закрепление/открепление сообщения"""
    if not can_access_chat(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    message = get_object_or_404(ChatMessage, id=message_id)
    
    # Только админы могут закреплять сообщения
    if request.user.role not in ('admin', 'superadmin'):
        return JsonResponse({'error': 'Только администраторы могут закреплять сообщения'}, status=403)
    
    message.is_pinned = not message.is_pinned
    message.save()
    
    return JsonResponse({
        'success': True,
        'is_pinned': message.is_pinned
    })


@login_required
def get_new_messages(request, room_id):
    """Получение новых сообщений (AJAX)"""
    if not can_access_chat(request.user):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    last_message_id = request.GET.get('last_message_id', 0)
    
    messages = ChatMessage.objects.filter(
        room=room,
        id__gt=last_message_id,
        is_deleted=False
    ).select_related('author').order_by('created_at')
    
    message_list = []
    for message in messages:
        message_list.append({
            'id': message.id,
            'content': message.content,
            'author': message.author.get_display_name(),
            'author_id': message.author.id,
            'created_at': message.created_at.strftime('%H:%M'),
            'can_edit': message.can_edit and message.author == request.user,
            'can_delete': message.can_delete or request.user.role in ('admin', 'superadmin'),
            'is_pinned': message.is_pinned,
        })
    
    # Обновляем статус прочтения
    if messages.exists():
        read_status, _ = ChatReadStatus.objects.get_or_create(
            user=request.user, 
            room=room
        )
        read_status.last_read_message = messages.last()
        read_status.save()
    
    return JsonResponse({
        'success': True,
        'messages': message_list
    })


@login_required
def get_unread_count(request):
    """Получение количества непрочитанных сообщений"""
    if not can_access_chat(request.user):
        return JsonResponse({'unread_count': 0})
    
    rooms = ChatRoom.objects.filter(is_active=True)
    total_unread = 0
    
    for room in rooms:
        read_status = ChatReadStatus.objects.filter(user=request.user, room=room).first()
        if read_status and read_status.last_read_message:
            unread = ChatMessage.objects.filter(
                room=room,
                created_at__gt=read_status.last_read_message.created_at,
                is_deleted=False
            ).exclude(author=request.user).count()
            total_unread += unread
        else:
            # Если нет статуса прочтения, считаем все сообщения кроме своих
            total_unread += ChatMessage.objects.filter(
                room=room,
                is_deleted=False
            ).exclude(author=request.user).count()
    
    return JsonResponse({'unread_count': total_unread})


# Для администраторов - управление комнатами
@admin_required
def room_management(request):
    """Управление комнатами чата"""
    rooms = ChatRoom.objects.all().order_by('-created_at')
    active_rooms_count = rooms.filter(is_active=True).count()
    
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Комната "{room.name}" создана')
            return redirect('chat_admin:room_management')
    else:
        form = ChatRoomForm()
    
    context = {
        'rooms': rooms,
        'active_rooms_count': active_rooms_count,
        'form': form,
        'page_title': 'Управление чатами',
        'active_menu': 'chat_management',
    }
    return render(request, 'chat/room_management.html', context)


@admin_required
def edit_room(request, room_id):
    """Редактирование комнаты"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f'Комната "{room.name}" обновлена')
            return redirect('chat:room_management')
    else:
        form = ChatRoomForm(instance=room)
    
    context = {
        'room': room,
        'form': form,
        'page_title': f'Редактирование комнаты - {room.name}',
    }
    return render(request, 'chat/edit_room.html', context)
