from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.core.mixins import mentor_required, admin_required, get_current_organization
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import calendar
from datetime import date

from apps.courses.models import Course
from .models import Lesson
from apps.core.mixins_substitute import check_substitute_access


from django import forms


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'lesson_date', 'start_time', 'end_time', 'room', 'meet_link', 'type', 'status', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'lesson_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'meet_link': forms.URLInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


def get_mentor_course_with_substitute_access(user, course_id):
    """
    Получение курса с проверкой прав доступа для заменяющего ментора
    """
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    
    # Проверяем, является ли пользователем основным ментором
    course = get_object_or_404(Course, pk=course_id)
    if course.mentor == user:
        return course
    
    # Проверяем, является ли пользователем заменяющим ментором
    if check_substitute_access(user, course_id):
        return course
    
    raise PermissionDenied("У вас нет прав доступа к этому курсу")


def get_mentor_course(user, course_id):
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def lessons_calendar(request, course_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)

    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    cal = calendar.monthcalendar(year, month)
    # Фильтруем уроки по организации
    current_org = get_current_organization(request.user)
    lessons = Lesson.objects.filter(
        organization=current_org,
        course=course,
        lesson_date__year=year,
        lesson_date__month=month,
    ).order_by('lesson_date', 'start_time') if current_org else Lesson.objects.none()

    lessons_by_day = {}
    for lesson in lessons:
        day = lesson.lesson_date.day
        lessons_by_day.setdefault(day, []).append(lesson)

    cal_with_lessons = []
    for week in cal:
        week_data = []
        for day in week:
            week_data.append({'day': day, 'lessons': lessons_by_day.get(day, []) if day != 0 else []})
        cal_with_lessons.append(week_data)

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    # Определяем, является ли пользователь заменяющим ментором
    is_substitute_mentor = course.mentor != request.user and request.user.role == 'mentor'

    context = {
        'course': course,
        'cal': cal,
        'cal_with_lessons': cal_with_lessons,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'lessons_by_day': lessons_by_day,
        'lessons': lessons,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
        'is_substitute_mentor': is_substitute_mentor,
        'page_title': 'Занятия',
        'active_menu': 'lessons',
    }
    return render(request, 'mentor/lessons/calendar.html', context)


@login_required
@mentor_required
def lesson_create(request, course_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    form = LessonForm(request.POST or None, initial={'lesson_date': request.GET.get('date', '')})
    if request.method == 'POST' and form.is_valid():
        lesson = form.save(commit=False)
        lesson.course = course
        lesson.created_by = request.user
        # Устанавливаем организацию
        current_org = get_current_organization(request.user)
        if current_org:
            lesson.organization = current_org
        lesson.save()
        messages.success(request, 'Занятие создано.')
        return redirect('lessons:calendar', course_id=course_id)
    return render(request, 'mentor/lessons/form.html', {
        'form': form, 'course': course, 'page_title': 'Новое занятие'
    })


@login_required
@mentor_required
@require_POST
def mark_lesson_completed(request, course_id, lesson_id):
    """Отметить урок как проведенный"""
    try:
        course = get_mentor_course_with_substitute_access(request.user, course_id)
        lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
        
        if lesson.status == 'scheduled':
            lesson.status = 'completed'
            lesson.save(update_fields=['status'])
            
            # Если есть замена, завершаем ее
            try:
                from apps.lessons.models_substitute import MentorSubstitution
                substitution = MentorSubstitution.objects.get(
                    lesson=lesson,
                    substitute_mentor=request.user,
                    status='confirmed'
                )
                substitution.complete()
            except MentorSubstitution.DoesNotExist:
                pass
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@mentor_required
def lesson_edit(request, course_id, lesson_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    form = LessonForm(request.POST or None, instance=lesson)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Занятие обновлено.')
        return redirect('lessons:calendar', course_id=course_id)
    return render(request, 'mentor/lessons/form.html', {
        'form': form, 'course': course, 'lesson': lesson, 'page_title': 'Редактировать занятие'
    })


@login_required
@mentor_required
def lesson_delete(request, course_id, lesson_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Занятие удалено.')
    return redirect('lessons:calendar', course_id=course_id)
