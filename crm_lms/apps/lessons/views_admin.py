from django.contrib.auth.decorators import login_required
from apps.core.mixins import admin_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
import calendar
from datetime import date

from apps.courses.models import Course
from .models import Lesson
from .views import LessonForm


def get_admin_course(user, course_id):
    """Проверка доступа админа к курсу"""
    if user.role != 'admin':
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут управлять курсами")
    return get_object_or_404(Course, pk=course_id)


@login_required
@admin_required
def admin_lessons_calendar(request, course_id):
    """Расписание уроков для администраторов"""
    course = get_admin_course(request.user, course_id)

    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    cal = calendar.monthcalendar(year, month)

    lessons = Lesson.objects.filter(
        course=course,
        lesson_date__year=year,
        lesson_date__month=month
    ).order_by('lesson_date', 'start_time')

    lessons_by_day = {}
    for lesson in lessons:
        day = lesson.lesson_date.day
        if day not in lessons_by_day:
            lessons_by_day[day] = []
        lessons_by_day[day].append(lesson)

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
        'page_title': 'Занятия',
        'active_menu': 'lessons',
    }
    return render(request, 'admin/lessons/calendar.html', context)


@login_required
@admin_required
def admin_lesson_create(request, course_id):
    """Создание урока для администраторов"""
    course = get_admin_course(request.user, course_id)
    form = LessonForm(request.POST or None, initial={'lesson_date': request.GET.get('date', '')})
    
    if request.method == 'POST' and form.is_valid():
        lesson = form.save(commit=False)
        lesson.course = course
        lesson.save()
        return redirect('admin_lessons:calendar', course_id=course.pk)
    
    context = {
        'course': course,
        'form': form,
        'page_title': 'Создание занятия',
        'active_menu': 'lessons',
    }
    return render(request, 'admin/lessons/create.html', context)


@login_required
@admin_required
def admin_lesson_edit(request, course_id, lesson_id):
    """Редактирование урока для администраторов"""
    course = get_admin_course(request.user, course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    form = LessonForm(request.POST or None, instance=lesson)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('admin_lessons:calendar', course_id=course.pk)
    
    context = {
        'course': course,
        'lesson': lesson,
        'form': form,
        'page_title': 'Редактирование занятия',
        'active_menu': 'lessons',
    }
    return render(request, 'admin/lessons/edit.html', context)


@login_required
@admin_required
def admin_lesson_delete(request, course_id, lesson_id):
    """Удаление урока для администраторов"""
    course = get_admin_course(request.user, course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    
    if request.method == 'POST':
        lesson.delete()
        return redirect('admin_lessons:calendar', course_id=course.pk)
    
    context = {
        'course': course,
        'lesson': lesson,
        'page_title': 'Удаление занятия',
        'active_menu': 'lessons',
    }
    return render(request, 'admin/lessons/delete.html', context)
