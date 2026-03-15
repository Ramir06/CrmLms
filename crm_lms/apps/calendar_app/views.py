import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET

from apps.lessons.models import Lesson
from apps.attendance.models import AttendanceRecord
from apps.courses.models import CourseStudent
from apps.core.mixins import admin_required


@login_required
def admin_calendar(request):
    from apps.courses.models import Course
    courses = Course.objects.filter(is_archived=False).order_by('title')
    return render(request, 'admin/calendar/index.html', {
        'page_title': 'Календарь',
        'courses': courses,
    })


@login_required
def mentor_calendar(request):
    return render(request, 'mentor/calendar/index.html', {'page_title': 'Расписание'})


@login_required
def calendar_events_api(request):
    """Return lessons as FullCalendar-compatible JSON events."""
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    lessons = Lesson.objects.select_related('course', 'course__mentor').all()

    if request.user.role == 'mentor':
        lessons = lessons.filter(course__mentor=request.user)

    if start_str:
        try:
            start_dt = date.fromisoformat(start_str[:10])
            lessons = lessons.filter(lesson_date__gte=start_dt)
        except ValueError:
            pass
    if end_str:
        try:
            end_dt = date.fromisoformat(end_str[:10])
            lessons = lessons.filter(lesson_date__lte=end_dt)
        except ValueError:
            pass

    events = []
    for lesson in lessons:
        color = lesson.course.color if lesson.course else '#7c3aed'
        title_parts = [lesson.course.title if lesson.course else 'Урок']
        if lesson.title:
            title_parts.append(lesson.title)

        events.append({
            'id': lesson.pk,
            'title': ' — '.join(title_parts),
            'start': f'{lesson.lesson_date}T{lesson.start_time}',
            'end': f'{lesson.lesson_date}T{lesson.end_time}',
            'color': color,
            'extendedProps': {
                'course': lesson.course.title if lesson.course else '',
                'mentor': lesson.course.mentor.get_display_name() if lesson.course and lesson.course.mentor else '',
                'room': lesson.room,
                'status': lesson.status,
                'meet_link': lesson.meet_link,
            }
        })

    return JsonResponse(events, safe=False)


@login_required
@require_GET
def lesson_drawer(request, pk):
    """Return partial HTML for the lesson drawer panel."""
    lesson = get_object_or_404(Lesson, pk=pk)

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
    for cs in students_in_course:
        ar = attendance_map.get(cs.student_id)
        students_data.append({
            'student': cs.student,
            'attendance': ar,
        })

    context = {
        'lesson': lesson,
        'students_data': students_data,
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

    return JsonResponse({'status': 'saved'})
