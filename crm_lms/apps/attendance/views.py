from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.core.mixins import mentor_required
from apps.courses.models import Course, CourseStudent
from apps.lessons.models import Lesson
from .models import AttendanceRecord


def get_mentor_course(user, course_id):
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def attendance_table(request, course_id):
    course = get_mentor_course(request.user, course_id)

    # Show ALL lessons regardless of status (scheduled, completed, etc.)
    lessons = Lesson.objects.filter(
        course=course
    ).exclude(status='cancelled').order_by('lesson_date', 'start_time')

    students = CourseStudent.objects.filter(
        course=course, status='active'
    ).select_related('student').order_by('student__full_name')

    # Build attendance matrix
    records = AttendanceRecord.objects.filter(lesson__in=lessons).select_related('student', 'lesson')
    record_map = {(r.lesson_id, r.student_id): r for r in records}

    matrix = []
    for cs in students:
        row = {'cs': cs, 'cells': []}
        present_count = 0
        for lesson in lessons:
            rec = record_map.get((lesson.pk, cs.student_id))
            row['cells'].append({
                'lesson_id': lesson.pk,
                'record': rec,
                'status': rec.attendance_status if rec else '',
            })
            if rec and rec.attendance_status == 'present':
                present_count += 1
        total = len(lessons)
        row['percent'] = round(present_count / total * 100) if total > 0 else 0
        matrix.append(row)

    context = {
        'course': course,
        'lessons': lessons,
        'matrix': matrix,
        'STATUS_CHOICES': AttendanceRecord.STATUS_CHOICES,
        'page_title': 'Посещаемость',
        'active_menu': 'attendance',
    }
    return render(request, 'mentor/attendance/table.html', context)


@login_required
@mentor_required
@require_POST
def save_attendance_bulk(request, course_id):
    course = get_mentor_course(request.user, course_id)
    active_students = CourseStudent.objects.filter(
        course=course, status='active'
    ).values_list('student_id', flat=True)
    active_student_ids = set(active_students)

    touched_lesson_ids = set()
    for key, value in request.POST.items():
        if key.startswith('att_'):
            parts = key.split('_')
            if len(parts) == 3:
                try:
                    lesson_id = int(parts[1])
                    student_id = int(parts[2])
                    if value:  # only save non-empty values
                        AttendanceRecord.objects.update_or_create(
                            lesson_id=lesson_id,
                            student_id=student_id,
                            defaults={'attendance_status': value},
                        )
                        touched_lesson_ids.add(lesson_id)
                except (ValueError, Exception):
                    pass

    # Auto-complete lessons where ALL active students have been marked
    for lesson_id in touched_lesson_ids:
        try:
            lesson = Lesson.objects.get(pk=lesson_id, course=course)
            marked_students = set(
                AttendanceRecord.objects.filter(lesson=lesson)
                .exclude(attendance_status='')
                .values_list('student_id', flat=True)
            )
            if active_student_ids and active_student_ids.issubset(marked_students):
                if lesson.status == 'scheduled':
                    lesson.status = 'completed'
                    lesson.save(update_fields=['status'])
        except Lesson.DoesNotExist:
            pass

    messages.success(request, 'Посещаемость сохранена.')
    return redirect('attendance:table', course_id=course_id)
