from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.core.mixins import mentor_required, admin_required
from apps.lessons.models import Lesson
from .models_substitute import MentorSubstitution, SubstituteAccess
from apps.accounts.models import CustomUser
from apps.mentors.models import MentorProfile
from django.db import models


@login_required
def substitute_mentor_view(request, course_id, lesson_id):
    """Страница замены ментора на уроке"""
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    
    # Проверяем права доступа
    if not can_manage_substitution(request.user, lesson):
        messages.error(request, 'У вас нет прав для управления заменами на этот урок')
        return redirect('lessons:calendar', course_id=lesson.course.pk)
    
    # Получаем текущего ментора урока
    current_mentor = lesson.course.mentor
    
    # Получаем доступных менторов для замены
    available_mentors = get_available_mentors_for_substitution(current_mentor, lesson)
    
    # Получаем существующие замены для этого урока
    existing_substitutions = MentorSubstitution.objects.filter(
        lesson=lesson,
        status__in=['pending', 'confirmed']
    ).select_related('substitute_mentor')
    
    context = {
        'lesson': lesson,
        'current_mentor': current_mentor,
        'available_mentors': available_mentors,
        'existing_substitutions': existing_substitutions,
        'page_title': f'Замена ментора - {lesson.title}'
    }
    
    return render(request, 'lessons/substitute_mentor.html', context)


@login_required
@require_POST
def create_substitution(request, course_id, lesson_id):
    """Создание замены ментора"""
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    
    if not can_manage_substitution(request.user, lesson):
        return JsonResponse({'error': 'Нет прав доступа'}, status=403)
    
    substitute_mentor_id = request.POST.get('substitute_mentor')
    reason = request.POST.get('reason', '')
    
    if not substitute_mentor_id:
        return JsonResponse({'error': 'Выберите ментора для замены'}, status=400)
    
    try:
        substitute_mentor = CustomUser.objects.get(
            pk=substitute_mentor_id, 
            role='mentor'
        )
        
        # Проверяем, что заменяющий ментор доступен
        if not is_mentor_available_for_substitution(substitute_mentor, lesson):
            return JsonResponse({'error': 'Ментор недоступен для замены'}, status=400)
        
        # Создаем замену
        substitution = MentorSubstitution.objects.create(
            lesson=lesson,
            original_mentor=lesson.course.mentor,
            substitute_mentor=substitute_mentor,
            reason=reason,
            created_by=request.user,
            status='pending'
        )
        
        # Создаем права доступа
        SubstituteAccess.objects.create(substitution=substitution)
        
        return JsonResponse({
            'success': True,
            'substitution_id': substitution.id,
            'substitute_name': f"{substitute_mentor.first_name} {substitute_mentor.last_name}".strip() or substitute_mentor.username
        })
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Ментор не найден'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def confirm_substitution(request, substitution_id):
    """Подтверждение замены"""
    substitution = get_object_or_404(MentorSubstitution, pk=substitution_id)
    
    # Проверяем права
    if not can_confirm_substitution(request.user, substitution):
        return JsonResponse({'error': 'Нет прав для подтверждения'}, status=403)
    
    substitution.confirm()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def cancel_substitution(request, substitution_id):
    """Отмена замены"""
    substitution = get_object_or_404(MentorSubstitution, pk=substitution_id)
    
    # Проверяем права
    if not can_cancel_substitution(request.user, substitution):
        return JsonResponse({'error': 'Нет прав для отмены'}, status=403)
    
    substitution.cancel()
    
    return JsonResponse({'success': True})


def can_manage_substitution(user, lesson):
    """Проверка прав на управление заменами"""
    if user.role == 'admin' or user.role == 'superadmin':
        return True
    
    # Основной ментор курса может управлять заменами
    if lesson.course.mentor == user:
        return True
    
    return False


def can_confirm_substitution(user, substitution):
    """Проверка прав на подтверждение замены"""
    if user.role == 'admin' or user.role == 'superadmin':
        return True
    
    # Заменяющий ментор может подтвердить свою замену
    if substitution.substitute_mentor == user:
        return True
    
    return False


def can_cancel_substitution(user, substitution):
    """Проверка прав на отмену замены"""
    if user.role == 'admin' or user.role == 'superadmin':
        return True
    
    # Создатель замены может отменить
    if substitution.created_by == user:
        return True
    
    # Основной ментор может отменить
    if substitution.original_mentor == user:
        return True
    
    return False


def get_available_mentors_for_substitution(current_mentor, lesson):
    """Получить доступных менторов для замены"""
    # Исключаем текущего ментора
    mentors = CustomUser.objects.filter(
        role='mentor',
        is_active=True
    ).exclude(pk=current_mentor.pk)
    
    # Можно добавить дополнительные фильтры:
    # - Специализация совпадает
    # - Свободное время в этот день
    # - Не занят на других уроках в это время
    
    return mentors


def is_mentor_available_for_substitution(mentor, lesson):
    """Проверить доступность ментора для замены"""
    # Проверяем, что у ментора нет других уроков в это время
    conflicting_lessons = Lesson.objects.filter(
        course__mentor=mentor,
        lesson_date=lesson.lesson_date,
        status__in=['scheduled', 'completed']
    ).filter(
        models.Q(start_time__lte=lesson.start_time, end_time__gt=lesson.start_time) |
        models.Q(start_time__lt=lesson.end_time, end_time__gte=lesson.end_time) |
        models.Q(start_time__gte=lesson.start_time, end_time__lte=lesson.end_time)
    )
    
    # Исключаем текущий урок (если ментор уже назначен)
    conflicting_lessons = conflicting_lessons.exclude(pk=lesson.pk)
    
    return not conflicting_lessons.exists()
