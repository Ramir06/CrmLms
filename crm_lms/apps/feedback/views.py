from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Feedback
from .telegram import send_feedback_to_telegram


def feedback_form(request, feedback_type):
    """Страница формы обратной связи"""
    
    type_labels = {
        'review': 'Оставить отзыв',
        'idea': 'Предложить идею',
        'bug': 'Сообщить о баге',
        'complaint': 'Подать жалобу',
        'suggestion': 'Предложить улучшение'
    }
    
    title = type_labels.get(feedback_type, 'Обратная связь')
    
    context = {
        'title': title,
        'feedback_type': feedback_type,
        'type_labels': type_labels,
    }
    
    return render(request, 'feedback/feedback_form.html', context)


def feedback_list(request):
    """Список всех типов обратной связи"""
    
    type_labels = {
        'review': 'Оставить отзыв',
        'idea': 'Предложить идею',
        'bug': 'Сообщить о баге',
        'complaint': 'Подать жалобу',
        'suggestion': 'Предложить улучшение'
    }
    
    context = {
        'title': 'Информация',
        'type_labels': type_labels,
    }
    
    return render(request, 'feedback/feedback_list.html', context)


def quick_feedback(request):
    """AJAX обработка быстрой обратной связи"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)
    
    try:
        # Получаем данные
        feedback_type = request.POST.get('type', '')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Базовая проверка
        if not feedback_type or not title or not description:
            return JsonResponse({
                'success': False,
                'error': f'Missing fields: type={feedback_type}, title={title}, desc={description}'
            }, status=400)
        
        # Создаем объект
        feedback = Feedback()
        feedback.type = feedback_type
        feedback.title = title
        feedback.description = description
        feedback.email = email
        feedback.user = request.user if request.user.is_authenticated else None
        feedback.save()
        
        # Отправка в Telegram
        try:
            send_feedback_to_telegram(feedback)
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Сообщение успешно отправлено!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)} - Type: {type(e).__name__}'
        }, status=500)


def feedback_success(request):
    """Страница успешной отправки"""
    return render(request, 'feedback/success.html')
