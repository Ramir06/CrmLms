from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.core.mixins import mentor_required
from apps.courses.models import Course, CourseStudent
from .models import Assignment, AssignmentSubmission, AssignmentGrade


from django import forms


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['section', 'title', 'description', 'max_score', 'due_date', 'order', 'is_required', 'is_visible']
        widgets = {
            'section': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            from apps.lectures.models import Section
            self.fields['section'].queryset = Section.objects.filter(course=course)


def get_mentor_course(user, course_id):
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def assignments_matrix(request, course_id):
    """Matrix view: rows=students, columns=assignments."""
    course = get_mentor_course(request.user, course_id)
    assignments = Assignment.objects.filter(course=course, is_visible=True).order_by('order', 'id')
    students = CourseStudent.objects.filter(
        course=course, status='active'
    ).select_related('student').order_by('student__full_name')

    # Build matrix
    matrix = []
    for cs in students:
        row = {'cs': cs, 'cells': []}
        for assignment in assignments:
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment, student=cs.student
            ).first()
            grade = None
            if submission and hasattr(submission, 'grade'):
                try:
                    grade = submission.grade
                except AssignmentGrade.DoesNotExist:
                    pass
            row['cells'].append({
                'assignment': assignment,
                'submission': submission,
                'grade': grade,
                'student_id': cs.pk,  # CourseStudent.pk, не Student.pk
            })
        matrix.append(row)

    context = {
        'course': course,
        'assignments': assignments,
        'matrix': matrix,
        'page_title': 'Проверка заданий',
        'active_menu': 'assignments',
    }
    return render(request, 'mentor/assignments/matrix.html', context)


@login_required
@mentor_required
def assignment_create(request, course_id):
    course = get_mentor_course(request.user, course_id)
    form = AssignmentForm(request.POST or None, course=course)
    if request.method == 'POST' and form.is_valid():
        assignment = form.save(commit=False)
        assignment.course = course
        assignment.save()
        messages.success(request, 'Задание создано.')
        return redirect('assignments:matrix', course_id=course_id)
    return render(request, 'mentor/assignments/form.html', {
        'form': form, 'course': course, 'page_title': 'Новое задание'
    })


@login_required
@mentor_required
def submission_review(request, submission_id):
    submission = get_object_or_404(AssignmentSubmission, pk=submission_id)
    course = submission.assignment.course
    if request.user.role not in ('admin', 'superadmin') and course.mentor != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    grade = None
    try:
        grade = submission.grade
    except AssignmentGrade.DoesNotExist:
        pass

    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')
        if score is not None:
            if grade:
                grade.score = score
                grade.comment = comment
                grade.checked_by = request.user
                grade.save()
            else:
                AssignmentGrade.objects.create(
                    submission=submission,
                    score=score,
                    comment=comment,
                    checked_by=request.user,
                )
            submission.status = 'checked'
            submission.save()
            messages.success(request, 'Оценка сохранена.')
            return redirect('assignments:matrix', course_id=course.pk)

    context = {
        'submission': submission,
        'grade': grade,
        'course': course,
        'page_title': f'Проверка: {submission.student.full_name}',
        'active_menu': 'assignments',
    }
    return render(request, 'mentor/assignments/submission_review.html', context)


@login_required
@mentor_required
@require_POST
def grade_submission_ajax(request, submission_id):
    """AJAX endpoint for grading a submission from the matrix modal."""
    submission = get_object_or_404(AssignmentSubmission, pk=submission_id)
    course = submission.assignment.course
    if request.user.role not in ('admin', 'superadmin') and course.mentor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    score = request.POST.get('score')
    comment = request.POST.get('comment', '')
    action = request.POST.get('action', 'accept')  # accept or reject

    if score is None or score == '':
        return JsonResponse({'error': 'Score is required'}, status=400)

    try:
        score_val = float(score)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid score'}, status=400)

    grade = None
    try:
        grade = submission.grade
    except AssignmentGrade.DoesNotExist:
        pass

    if grade:
        grade.score = score_val
        grade.comment = comment
        grade.checked_by = request.user
        grade.save()
    else:
        AssignmentGrade.objects.create(
            submission=submission,
            score=score_val,
            comment=comment,
            checked_by=request.user,
        )

    if action == 'reject':
        submission.status = 'revision'
    else:
        submission.status = 'checked'
    submission.save()

    return JsonResponse({
        'ok': True,
        'score': str(score_val),
        'max_score': submission.assignment.max_score,
        'status': submission.status,
    })


@login_required
@mentor_required
@require_POST
def create_grade_ajax(request, course_id, assignment_id, student_id):
    """Create grade for assignment without submission."""
    print(f"DEBUG: create_grade_ajax called with course_id={course_id}, assignment_id={assignment_id}, student_id={student_id}")
    
    course = get_mentor_course(request.user, course_id)
    assignment = get_object_or_404(Assignment, pk=assignment_id, course=course)
    course_student = get_object_or_404(CourseStudent, pk=student_id, course=course)
    student = course_student.student
    
    print(f"DEBUG: Found course={course.title}, assignment={assignment.title}, student={student.full_name}")
    
    score = request.POST.get('score')
    comment = request.POST.get('comment', '')
    action = request.POST.get('action', 'accept')

    if score is None or score == '':
        return JsonResponse({'error': 'Score is required'}, status=400)

    try:
        score_val = float(score)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid score'}, status=400)

    # Create submission if it doesn't exist
    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=student,
        defaults={
            'status': 'checked' if action == 'accept' else 'revision',
            'submitted_at': timezone.now(),
        }
    )

    # Update status if submission existed
    if not created:
        submission.status = 'checked' if action == 'accept' else 'revision'
        submission.save()

    # Create or update grade
    grade, grade_created = AssignmentGrade.objects.get_or_create(
        submission=submission,
        defaults={
            'score': score_val,
            'comment': comment,
            'checked_by': request.user,
        }
    )

    if not grade_created:
        grade.score = score_val
        grade.comment = comment
        grade.checked_by = request.user
        grade.save()

    return JsonResponse({
        'ok': True,
        'score': str(score_val),
        'max_score': assignment.max_score,
        'status': submission.status,
        'submission_id': submission.pk,
    })


@login_required
@mentor_required
def student_stats(request, course_id):
    """Calculate average scores and ranking for students."""
    course = get_mentor_course(request.user, course_id)
    
    # Get all active students in the course
    course_students = CourseStudent.objects.filter(
        course=course, 
        status='active'
    ).select_related('student').order_by('student__full_name')
    
    # Get all assignments for the course
    assignments = Assignment.objects.filter(course=course, is_visible=True)
    
    student_stats = []
    
    for cs in course_students:
        student = cs.student
        
        # Calculate total score and max possible score
        total_score = 0
        total_max_score = 0
        assignments_count = 0
        graded_assignments = 0
        
        for assignment in assignments:
            assignments_count += 1
            total_max_score += assignment.max_score
            
            # Get the latest submission and grade for this assignment
            try:
                submission = AssignmentSubmission.objects.filter(
                    assignment=assignment,
                    student=student
                ).latest('submitted_at')
                
                if submission.grade:
                    total_score += submission.grade.score
                    graded_assignments += 1
            except AssignmentSubmission.DoesNotExist:
                # No submission, score is 0
                pass
        
        # Calculate average score
        avg_score = 0
        if total_max_score > 0:
            avg_score = float(total_score) / float(total_max_score) * 100  # Percentage
        
        student_stats.append({
            'student': student,
            'total_score': total_score,
            'total_max_score': total_max_score,
            'avg_score_percent': round(avg_score, 1),
            'graded_assignments': graded_assignments,
            'total_assignments': assignments_count,
            'completion_rate': round((graded_assignments / assignments_count * 100), 1) if assignments_count > 0 else 0
        })
    
    # Sort by average score (descending) for ranking
    student_stats.sort(key=lambda x: x['avg_score_percent'], reverse=True)
    
    # Add ranking
    for i, stat in enumerate(student_stats, 1):
        stat['rank'] = i
    
    # Calculate overall statistics
    total_students = len(student_stats)
    avg_score_all = 0
    avg_completion_all = 0
    
    if total_students > 0:
        avg_score_all = float(sum(stat['avg_score_percent'] for stat in student_stats)) / total_students
        avg_completion_all = float(sum(stat['completion_rate'] for stat in student_stats)) / total_students
    
    context = {
        'course': course,
        'student_stats': student_stats,
        'total_students': total_students,
        'avg_score_all': round(avg_score_all, 1),
        'avg_completion_all': round(avg_completion_all, 1),
        'page_title': 'Рейтинг студентов',
        'active_menu': 'rating',
    }
    
    return render(request, 'mentor/assignments/student_stats.html', context)
