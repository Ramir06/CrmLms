import json
from datetime import date, timedelta
from django.db import models

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages

from apps.lessons.models import Lesson
from apps.attendance.models import AttendanceRecord
from apps.courses.models import CourseStudent
from apps.core.mixins import admin_required, get_current_organization, organization_context
from .models import Event
from .forms import EventForm


@login_required
@organization_context
def admin_calendar(request):
    from apps.courses.models import Course
    # Фильтруем курсы по текущей организации
    current_org = get_current_organization(request.user)
    courses = Course.objects.filter(organization=current_org, is_archived=False).order_by('title') if current_org else Course.objects.none()
    
    # Форма для создания мероприятия
    event_form = EventForm(organization=current_org)
    
    # Отладочная информация
    print(f"DEBUG calendar: current_org = {current_org}")
    print(f"DEBUG calendar: request.current_organization = {getattr(request, 'current_organization', 'None')}")
    
    return render(request, 'admin/calendar/index.html', {
        'page_title': 'Календарь',
        'courses': courses,
        'current_organization': current_org,
        'event_form': event_form,
    })


@login_required
def mentor_calendar(request):
    return render(request, 'mentor/calendar/index.html', {'page_title': 'Расписание'})


@login_required
def calendar_events_api(request):
    """Return lessons and events as FullCalendar-compatible JSON events."""
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    # Фильтруем уроки по текущей организации
    current_org = get_current_organization(request.user)
    lessons = Lesson.objects.filter(organization=current_org).select_related('course', 'course__mentor') if current_org else Lesson.objects.none()
    events = Event.objects.filter(organization=current_org) if current_org else Event.objects.none()

    if request.user.role == 'mentor':
        lessons = lessons.filter(course__mentor=request.user)
        # Для менторов показываем только мероприятия, предназначенные для них или общие
        events = events.filter(
            models.Q(target_type='mentor') | 
            models.Q(target_type='organization') | 
            models.Q(target_user=request.user)
        )

    if start_str:
        try:
            start_dt = date.fromisoformat(start_str[:10])
            lessons = lessons.filter(lesson_date__gte=start_dt)
            events = events.filter(date__gte=start_dt)
        except ValueError:
            pass
    if end_str:
        try:
            end_dt = date.fromisoformat(end_str[:10])
            lessons = lessons.filter(lesson_date__lte=end_dt)
            events = events.filter(date__lte=end_dt)
        except ValueError:
            pass

    result = []

    # Добавляем уроки
    for lesson in lessons:
        color = lesson.course.color if lesson.course else '#7c3aed'
        title_parts = [lesson.course.title if lesson.course else 'Урок']
        if lesson.title:
            title_parts.append(lesson.title)

        result.append({
            'id': f'lesson_{lesson.pk}',
            'title': ' — '.join(title_parts),
            'start': f'{lesson.lesson_date}T{lesson.start_time}',
            'end': f'{lesson.lesson_date}T{lesson.end_time}',
            'color': color,
            'extendedProps': {
                'type': 'lesson',
                'course': lesson.course.title if lesson.course else '',
                'mentor': lesson.course.mentor.get_display_name() if lesson.course and lesson.course.mentor else '',
                'room': lesson.room,
                'status': lesson.status,
                'meet_link': lesson.meet_link,
            }
        })

    # Добавляем мероприятия
    for event in events:
        result.append({
            'id': f'event_{event.pk}',
            'title': event.title,
            'start': f'{event.date}T{event.start_time}',
            'end': f'{event.date}T{event.end_time}',
            'color': event.color,
            'extendedProps': {
                'type': 'event',
                'description': event.description,
                'target_type': event.get_target_type_display(),
                'target_user': event.target_user.get_display_name() if event.target_user else '',
            }
        })

    return JsonResponse(result, safe=False)


@login_required
@require_GET
def lesson_drawer(request, pk):
    """Return partial HTML for the lesson drawer panel."""
    try:
        lesson = Lesson.objects.get(pk=pk)
    except Lesson.DoesNotExist:
        from django.http import Http404
        raise Http404(f'Урок с ID {pk} не найден')

    # Check mentor access
    if request.user.role == 'mentor' and lesson.course.mentor != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    students_in_course = CourseStudent.objects.filter(
        course=lesson.course, status='active'
    ).select_related('student')

    attendance_map = {
        ar.student_id: ar
        for ar in AttendanceRecord.objects.filter(lesson=lesson)
    }

    students_data = []
    present_count = 0
    for cs in students_in_course:
        ar = attendance_map.get(cs.student_id)
        if ar and ar.attendance_status == 'present':
            present_count += 1
        students_data.append({
            'student': cs.student,
            'attendance': ar,
        })

    context = {
        'lesson': lesson,
        'students_data': students_data,
        'present_count': present_count,
        'user': request.user,
    }
    return render(request, 'includes/drawer_lesson_detail.html', context)


@login_required
def save_attendance(request, pk):
    """Save attendance for a lesson via POST."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    lesson = get_object_or_404(Lesson, pk=pk)

    if request.user.role == 'mentor' and lesson.course.mentor != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    import json as j
    try:
        data = j.loads(request.body)
        records = data.get('records', [])
    except Exception:
        # fallback to form data
        records = []
        for key, val in request.POST.items():
            if key.startswith('student_'):
                student_id = int(key.replace('student_', ''))
                records.append({'student_id': student_id, 'status': val})

    for rec in records:
        student_id = rec.get('student_id')
        status = rec.get('status', 'absent')
        AttendanceRecord.objects.update_or_create(
            lesson=lesson,
            student_id=student_id,
            defaults={'attendance_status': status},
        )

    # Auto-complete lesson if 90%+ of active students are marked
    try:
        from apps.courses.models import CourseStudent
        from apps.lessons.models_substitute import MentorSubstitution
        
        active_students = set(
            CourseStudent.objects.filter(
                course=lesson.course,
                status='active'
            ).values_list('student_id', flat=True)
        )
        
        marked_students = set(
            AttendanceRecord.objects.filter(lesson=lesson)
            .exclude(attendance_status='')
            .values_list('student_id', flat=True)
        )
        
        if active_students and len(active_students) > 0:
            marked_percentage = len(marked_students & active_students) / len(active_students) * 100
            
            if marked_percentage >= 90 and lesson.status == 'scheduled':
                lesson.status = 'completed'
                lesson.save(update_fields=['status'])
                
                try:
                    substitution = MentorSubstitution.objects.get(
                        lesson=lesson,
                        substitute_mentor=request.user,
                        status='confirmed'
                    )
                    substitution.complete()
                except MentorSubstitution.DoesNotExist:
                    pass
    except Exception as e:
        print(f"Error auto-completing lesson: {e}")

    return JsonResponse({'status': 'saved'})


@login_required
@admin_required
@require_POST
def create_event(request):
    """Создание нового мероприятия"""
    current_org = get_current_organization(request.user)
    
    if not current_org:
        return JsonResponse({'error': 'Организация не найдена'}, status=400)
    
    form = EventForm(request.POST, organization=current_org)
    
    if form.is_valid():
        event = form.save(commit=False)
        event.organization = current_org
        event.created_by = request.user
        event.save()
        
        return JsonResponse({
            'status': 'success',
            'event': {
                'id': event.id,
                'title': event.title,
                'date': event.date.strftime('%Y-%m-%d'),
                'start_time': event.start_time.strftime('%H:%M'),
                'end_time': event.end_time.strftime('%H:%M'),
                'target_type': event.get_target_type_display(),
                'color': event.color,
            }
        })
    else:
        return JsonResponse({
            'status': 'error',
            'errors': dict(form.errors)
        }, status=400)
