from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from django.contrib import messages as django_messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse_lazy
from django.utils import timezone
from apps.courses.models import Course, CourseStudent
from apps.lectures.models import Section, Material
from apps.quizzes.models import Quiz, QuizAttempt
from apps.attendance.models import AttendanceRecord
from apps.lessons.models import Lesson
from apps.assignments.models import Assignment, AssignmentSubmission


def get_student_profile(user):
    """Get the Student model instance linked to this user."""
    if not user.is_student:
        return None
    return getattr(user, 'student_profile', None)


@login_required
def student_dashboard(request):
    """Student dashboard with their courses, recent activity, and stats."""
    if not request.user.is_student:
        return HttpResponseRedirect(reverse_lazy('dashboard:index'))

    student = get_student_profile(request.user)
    if not student:
        raise Http404('Student profile not found')

    enrollments = CourseStudent.objects.filter(
        student=student,
        status='active'
    ).select_related('course', 'course__mentor').order_by('-joined_at')

    recent_quizzes = QuizAttempt.objects.filter(
        course_student__student=student
    ).select_related('quiz', 'course_student__course').order_by('-submitted_at')[:5]

    # Recent assignments (pending, across all courses)
    from apps.assignments.models import Assignment, AssignmentSubmission, AssignmentGrade
    active_course_ids = enrollments.values_list('course_id', flat=True)
    recent_assignments = Assignment.objects.filter(
        course_id__in=active_course_ids, is_visible=True
    ).select_related('course').order_by('-due_date', '-id')[:5]

    # Check which have submissions
    my_submissions = AssignmentSubmission.objects.filter(
        assignment__in=recent_assignments, student=student
    ).values_list('assignment_id', flat=True)
    submitted_ids = set(my_submissions)

    assignment_list = []
    for a in recent_assignments:
        assignment_list.append({
            'assignment': a,
            'submitted': a.pk in submitted_ids,
        })

    # Recent grades
    recent_grades = AssignmentGrade.objects.filter(
        submission__student=student,
        submission__assignment__course_id__in=active_course_ids,
    ).select_related(
        'submission__assignment', 'submission__assignment__course'
    ).order_by('-checked_at')[:5]

    context = {
        'enrollments': enrollments,
        'recent_quizzes': recent_quizzes,
        'recent_assignments': assignment_list,
        'recent_grades': recent_grades,
        'student': student,
        'page_title': 'Мой кабинет',
    }
    return render(request, 'students/dashboard.html', context)


@login_required
def course_detail(request, course_id):
    """Student view of a single course with materials and progress."""
    if not request.user.is_student:
        return HttpResponseRedirect(reverse_lazy('dashboard:index'))

    student = get_student_profile(request.user)
    if not student:
        raise Http404('Student profile not found')

    enrollment = get_object_or_404(
        CourseStudent,
        student=student,
        course_id=course_id,
        status='active'
    )
    course = enrollment.course
    sections = Section.objects.filter(
        course=course,
        is_visible=True
    ).prefetch_related('materials').order_by('order')

    # Get quiz attempts for this course
    attempts = QuizAttempt.objects.filter(
        course_student=enrollment
    ).select_related('quiz').order_by('-submitted_at')

    context = {
        'course': course,
        'enrollment': enrollment,
        'sections': sections,
        'attempts': attempts,
        'page_title': course.title,
    }
    return render(request, 'students/course_detail.html', context)


@login_required
def material_detail(request, course_id, material_id):
    """Student view of a specific material."""
    if not request.user.is_student:
        return HttpResponseRedirect(reverse_lazy('dashboard:index'))

    student = get_student_profile(request.user)
    if not student:
        raise Http404('Student profile not found')

    enrollment = get_object_or_404(
        CourseStudent,
        student=student,
        course_id=course_id,
        status='active'
    )
    material = get_object_or_404(
        Material,
        pk=material_id,
        section__course_id=course_id,
        is_visible=True
    )
    course = material.section.course

    # Prev/next navigation within the same section
    section_materials = Material.objects.filter(
        section=material.section, is_visible=True
    ).order_by('order', 'id')
    prev_material = section_materials.filter(order__lt=material.order).last()
    next_material = section_materials.filter(order__gt=material.order).first()

    context = {
        'course': course,
        'enrollment': enrollment,
        'material': material,
        'prev_material': prev_material,
        'next_material': next_material,
        'page_title': material.title,
    }
    return render(request, 'students/material_detail.html', context)


def student_logout(request):
    """Logout for students."""
    logout(request)
    return HttpResponseRedirect(reverse_lazy('accounts:login'))


@login_required
def student_attendance(request, course_id):
    """Student view of their attendance for a specific course."""
    if not request.user.is_student:
        return HttpResponseRedirect(reverse_lazy('dashboard:index'))

    student = get_student_profile(request.user)
    if not student:
        raise Http404('Student profile not found')

    enrollment = get_object_or_404(
        CourseStudent,
        student=student,
        course_id=course_id,
        status='active'
    )
    course = enrollment.course

    # Show ALL lessons regardless of status, exclude cancelled
    lessons = Lesson.objects.filter(
        course=course
    ).exclude(status='cancelled').order_by('lesson_date', 'start_time')

    records = AttendanceRecord.objects.filter(
        lesson__in=lessons, student=student
    ).select_related('lesson')
    record_map = {r.lesson_id: r for r in records}

    attendance_data = []
    present_count = 0
    for lesson in lessons:
        rec = record_map.get(lesson.pk)
        if rec:
            status = rec.attendance_status
        elif lesson.status == 'scheduled':
            status = 'pending'  # not yet conducted
        else:
            status = 'absent'
        attendance_data.append({
            'lesson': lesson,
            'status': status,
            'lesson_status': lesson.status,
            'comment': rec.comment if rec else '',
        })
        if status == 'present':
            present_count += 1

    total = len(lessons)
    percent = round(present_count / total * 100) if total > 0 else 0

    context = {
        'course': course,
        'enrollment': enrollment,
        'student': student,
        'attendance_data': attendance_data,
        'present_count': present_count,
        'total_lessons': total,
        'percent': percent,
        'page_title': 'Посещаемость',
    }
    return render(request, 'students/attendance.html', context)


@login_required
def student_grades(request, course_id):
    """Student view of their grades for a specific course."""
    if not request.user.is_student:
        return HttpResponseRedirect(reverse_lazy('dashboard:index'))

    student = get_student_profile(request.user)
    if not student:
        raise Http404('Student profile not found')

    enrollment = get_object_or_404(
        CourseStudent,
        student=student,
        course_id=course_id,
        status='active'
    )
    course = enrollment.course

    from apps.rating.models import StudentRating
    rating = StudentRating.objects.filter(course=course, student=student).first()

    from apps.assignments.models import Assignment, AssignmentSubmission
    assignments = Assignment.objects.filter(course=course).order_by('order', 'id')
    submissions = AssignmentSubmission.objects.filter(
        assignment__in=assignments, student=student
    ).select_related('assignment')
    # Prefetch grades safely
    sub_map = {}
    for s in submissions:
        try:
            s._cached_grade = s.grade
        except Exception:
            s._cached_grade = None
        sub_map[s.assignment_id] = s

    grades_data = []
    total_earned = 0
    total_max = 0
    checked_count = 0
    for assignment in assignments:
        sub = sub_map.get(assignment.pk)
        grade_obj = getattr(sub, '_cached_grade', None) if sub else None
        score = float(grade_obj.score) if grade_obj else None
        is_full = score is not None and score >= assignment.max_score
        grades_data.append({
            'assignment': assignment,
            'submission': sub,
            'score': grade_obj.score if grade_obj else None,
            'max_score': assignment.max_score,
            'comment': grade_obj.comment if grade_obj else '',
            'status': sub.status if sub else 'not_submitted',
            'is_full_score': is_full,
        })
        total_max += assignment.max_score
        if score is not None:
            total_earned += score
            checked_count += 1

    # Quiz attempts for this course
    quiz_attempts = QuizAttempt.objects.filter(
        course_student=enrollment
    ).select_related('quiz').order_by('-submitted_at')

    # Best quiz results per quiz
    quiz_best = {}
    for att in quiz_attempts:
        if att.quiz_id not in quiz_best or att.percentage > quiz_best[att.quiz_id].percentage:
            quiz_best[att.quiz_id] = att
    quiz_results = list(quiz_best.values())

    context = {
        'course': course,
        'enrollment': enrollment,
        'student': student,
        'rating': rating,
        'grades_data': grades_data,
        'quiz_results': quiz_results,
        'total_earned': total_earned,
        'total_max': total_max,
        'checked_count': checked_count,
        'assignments_count': len(assignments),
        'page_title': 'Оценки',
    }
    return render(request, 'students/grades.html', context)


def _get_student_or_redirect(request):
    """Helper: returns (student, None) or (None, redirect_response)."""
    if not request.user.is_student:
        return None, HttpResponseRedirect(reverse_lazy('dashboard:index'))
    student = get_student_profile(request.user)
    if not student:
        raise Http404('Student profile not found')
    return student, None


def _get_enrollment(student, course_id):
    """Helper: returns enrollment for student + course."""
    return get_object_or_404(
        CourseStudent, student=student, course_id=course_id, status='active'
    )


# ─── Schedule ───────────────────────────────────────────────────
@login_required
def student_schedule(request):
    """Student schedule: upcoming and recent lessons across all enrolled courses."""
    student, redir = _get_student_or_redirect(request)
    if redir:
        return redir

    enrollments = CourseStudent.objects.filter(
        student=student, status='active'
    ).select_related('course')
    course_ids = [e.course_id for e in enrollments]

    today = timezone.localdate()
    upcoming = Lesson.objects.filter(
        course_id__in=course_ids,
        lesson_date__gte=today,
        status__in=['scheduled', 'completed'],
    ).select_related('course').order_by('lesson_date', 'start_time')[:30]

    past_qs = Lesson.objects.filter(
        course_id__in=course_ids,
        lesson_date__lt=today,
        status='completed',
    ).select_related('course').order_by('-lesson_date', '-start_time')[:15]

    # Attendance map for past lessons
    records = AttendanceRecord.objects.filter(
        lesson__in=past_qs, student=student
    )
    att_map = {r.lesson_id: r.attendance_status for r in records}

    past = []
    for lesson in past_qs:
        lesson.att_status = att_map.get(lesson.pk, '')
        past.append(lesson)

    context = {
        'upcoming': upcoming,
        'past': past,
        'today': today,
        'page_title': 'Расписание',
    }
    return render(request, 'students/schedule.html', context)


# ─── Lesson detail ──────────────────────────────────────────────
@login_required
def student_lesson_detail(request, course_id, lesson_id):
    """Student view of a single lesson: topic, description, meet link, attendance."""
    student, redir = _get_student_or_redirect(request)
    if redir:
        return redir

    enrollment = _get_enrollment(student, course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course_id=course_id)

    att_record = AttendanceRecord.objects.filter(
        lesson=lesson, student=student
    ).first()

    context = {
        'course': enrollment.course,
        'enrollment': enrollment,
        'lesson': lesson,
        'att_record': att_record,
        'page_title': lesson.title or f'Занятие {lesson.lesson_date}',
    }
    return render(request, 'students/lesson_detail.html', context)


# ─── Assignments list ───────────────────────────────────────────
@login_required
def student_assignments(request, course_id):
    """Student list of all assignments for a course with submission status."""
    student, redir = _get_student_or_redirect(request)
    if redir:
        return redir

    enrollment = _get_enrollment(student, course_id)
    course = enrollment.course

    assignments = Assignment.objects.filter(
        course=course, is_visible=True
    ).order_by('order', 'id')

    submissions = AssignmentSubmission.objects.filter(
        assignment__in=assignments, student=student
    ).select_related('grade')
    sub_map = {s.assignment_id: s for s in submissions}

    today = timezone.localdate()
    assignments_data = []
    for a in assignments:
        sub = sub_map.get(a.pk)
        grade_obj = None
        if sub:
            try:
                grade_obj = sub.grade
            except Exception:
                pass
        assignments_data.append({
            'assignment': a,
            'submission': sub,
            'grade': grade_obj,
            'status': sub.status if sub else 'not_submitted',
            'is_overdue': a.due_date and a.due_date < today and (not sub or sub.status == 'not_submitted'),
        })

    context = {
        'course': course,
        'enrollment': enrollment,
        'assignments_data': assignments_data,
        'page_title': 'Задания',
    }
    return render(request, 'students/assignments.html', context)


# ─── Assignment submit ──────────────────────────────────────────
@login_required
def student_assignment_submit(request, course_id, assignment_id):
    """Student submits (or re-submits) an assignment."""
    student, redir = _get_student_or_redirect(request)
    if redir:
        return redir

    enrollment = _get_enrollment(student, course_id)
    course = enrollment.course
    assignment = get_object_or_404(
        Assignment, pk=assignment_id, course=course, is_visible=True
    )

    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment, student=student,
        defaults={'status': 'not_submitted'}
    )

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text', '').strip()
        file = request.FILES.get('file')
        if answer_text or file:
            submission.answer_text = answer_text
            if file:
                submission.file = file
            submission.status = 'submitted'
            submission.submitted_at = timezone.now()
            submission.save()
            django_messages.success(request, 'Задание отправлено!')
            return redirect('students:assignments', course_id=course_id)
        else:
            django_messages.error(request, 'Заполните ответ или прикрепите файл.')

    context = {
        'course': course,
        'enrollment': enrollment,
        'assignment': assignment,
        'submission': submission,
        'page_title': assignment.title,
    }
    return render(request, 'students/assignment_submit.html', context)


# ─── Quizzes list ───────────────────────────────────────────────
@login_required
def student_quizzes(request, course_id):
    """Student list of all quizzes for a course."""
    student, redir = _get_student_or_redirect(request)
    if redir:
        return redir

    enrollment = _get_enrollment(student, course_id)
    course = enrollment.course

    quizzes = Quiz.objects.filter(course=course, is_active=True).order_by('-created_at')

    attempts = QuizAttempt.objects.filter(
        course_student=enrollment
    ).select_related('quiz')
    attempt_map = {}
    for att in attempts:
        attempt_map.setdefault(att.quiz_id, []).append(att)

    quizzes_data = []
    for q in quizzes:
        q_attempts = attempt_map.get(q.pk, [])
        best = max(q_attempts, key=lambda a: a.percentage, default=None) if q_attempts else None
        quizzes_data.append({
            'quiz': q,
            'attempts_count': len(q_attempts),
            'best': best,
        })

    context = {
        'course': course,
        'enrollment': enrollment,
        'quizzes_data': quizzes_data,
        'page_title': 'Тесты',
    }
    return render(request, 'students/quizzes.html', context)


# ─── Quiz start ─────────────────────────────────────────────────
@login_required
def student_quiz_start(request, course_id, quiz_id):
    """Create a new quiz attempt and redirect to quiz-taking page."""
    student, redir = _get_student_or_redirect(request)
    if redir:
        return redir

    enrollment = _get_enrollment(student, course_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, course_id=course_id, is_active=True)

    # Create new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        course_student=enrollment,
        max_score=quiz.total_points(),
    )
    return redirect('quiz_take', token=attempt.token)
