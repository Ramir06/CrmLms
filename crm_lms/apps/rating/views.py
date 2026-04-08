from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg

from apps.core.mixins import mentor_required
from apps.courses.models import Course, CourseStudent
from apps.assignments.models import Assignment, AssignmentSubmission, AssignmentGrade
from .models import StudentRating


def get_mentor_course(user, course_id):
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def rating_table(request, course_id):
    course = get_mentor_course(request.user, course_id)

    students = CourseStudent.objects.filter(
        course=course, status='active'
    ).select_related('student').order_by('student__full_name')

    assignments = Assignment.objects.filter(course=course).order_by('order', 'id')

    submissions = AssignmentSubmission.objects.filter(
        assignment__in=assignments,
        student__in=[cs.student for cs in students],
    ).select_related('assignment', 'student', 'grade')
    sub_map = {(s.assignment_id, s.student_id): s for s in submissions}

    ratings = StudentRating.objects.filter(course=course).select_related('student')
    rating_map = {r.student_id: r for r in ratings}

    grades_matrix = []
    for cs in students:
        cells = []
        for a in assignments:
            sub = sub_map.get((a.pk, cs.student_id))
            grade_obj = getattr(sub, 'grade', None) if sub else None
            score = grade_obj.score if grade_obj else None
            percent = (float(score) / a.max_score * 100) if score is not None and a.max_score else None
            cells.append({
                'score': score,
                'max_score': a.max_score,
                'percent': percent,
                'status': sub.status if sub else 'not_submitted',
            })
        grades_matrix.append({
            'student_name': cs.student.full_name,
            'cells': cells,
            'rating': rating_map.get(cs.student_id),
        })

    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'assignments': assignments,
        'grades_matrix': grades_matrix,
        'page_title': 'Оценки',
        'active_menu': 'rating',
    }
    return render(request, 'mentor/rating/table.html', context)
