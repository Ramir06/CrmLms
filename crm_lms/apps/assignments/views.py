from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from apps.core.mixins import mentor_required
from apps.courses.models import Course, CourseStudent
from .models import Assignment, AssignmentSubmission, AssignmentGrade
from .forms import AssignmentForm
from apps.core.ai_service import nvidia_ai_service


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
            
            # Check for quiz results if assignment is linked to a quiz
            quiz_score = None
            if assignment.quiz:
                quiz_score = assignment.get_quiz_score(cs.student)
                
            row['cells'].append({
                'assignment': assignment,
                'submission': submission,
                'grade': grade,
                'quiz_score': quiz_score,
                'student_id': cs.pk,  # CourseStudent.pk, не Student.pk
                'grade_percentage': grade and int((grade.score / assignment.max_score) * 100) if grade else None,
                'quiz_percentage': quiz_score and quiz_score.percentage if quiz_score else None,
            })
        matrix.append(row)

    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'assignments': assignments,
        'matrix': matrix,
        'page_title': 'Оценки',
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
def assignment_solutions(request, course_id, assignment_id):
    """Show solutions for a specific assignment."""
    course = get_mentor_course(request.user, course_id)
    assignment = get_object_or_404(Assignment, pk=assignment_id, course=course)
    
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).exclude(status='not_submitted').select_related('student', 'grade').order_by('-submitted_at')
    
    context = {
        'course': course,
        'current_course': course,
        'assignment': assignment,
        'submissions': submissions,
        'page_title': f'Решения для задачи: {assignment.title}',
        'active_menu': 'assignments',
    }
    
    return render(request, 'mentor/assignments/solutions.html', context)


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
        'current_course': course,  # Добавляем для навбара
        'assignment': submission.assignment,
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
        'current_course': course,  # Добавляем для навбара
        'student_stats': student_stats,
        'total_students': total_students,
        'avg_score_all': round(avg_score_all, 1),
        'avg_completion_all': round(avg_completion_all, 1),
        'page_title': 'Рейтинг студентов',
        'active_menu': 'rating',
    }
    
    return render(request, 'mentor/assignments/student_stats.html', context)


@login_required
@mentor_required
@require_POST
def ai_check_submission(request, submission_id):
    """AI проверка задания"""
    submission = get_object_or_404(AssignmentSubmission, pk=submission_id)
    course = submission.assignment.course
    
    # Проверяем права доступа
    if request.user.role not in ('admin', 'superadmin') and course.mentor != request.user:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    # Проверяем, есть ли ответ для проверки
    if not submission.answer_text and not submission.file:
        return JsonResponse({'error': 'Нет ответа для проверки'}, status=400)
    
    try:
        # Подготавливаем текст ответа
        answer_text = submission.answer_text
        if submission.file:
            try:
                # Если есть файл, пытаемся прочитать его содержимое
                answer_text += f"\n\n[Файл: {submission.file.name}]"
                # Здесь можно добавить логику чтения файла в зависимости от типа
            except Exception as e:
                print(f"Error reading file: {e}")
        
        # Получаем критерии оценки из описания задания
        criteria = ""
        if submission.assignment.description:
            criteria = submission.assignment.description
        
        # Вызываем AI для проверки
        ai_result = nvidia_ai_service.check_assignment(
            assignment_text=submission.assignment.description or submission.assignment.title,
            student_answer=answer_text,
            criteria=criteria
        )
        
        if 'error' in ai_result:
            return JsonResponse({'error': f'AI ошибка: {ai_result["error"]}'}, status=500)
        
        # Создаем или обновляем оценку
        grade, created = AssignmentGrade.objects.get_or_create(
            submission=submission,
            defaults={
                'score': ai_result.get('score', 0),
                'comment': ai_result.get('feedback', ''),
                'checked_by': request.user,
                'ai_graded': True,
                'ai_confidence': ai_result.get('confidence', 80),
                'ai_feedback': ai_result,
                'ai_strengths': ', '.join(ai_result.get('strengths', [])),
                'ai_weaknesses': ', '.join(ai_result.get('weaknesses', [])),
                'ai_suggestions': ', '.join(ai_result.get('recommendations', [])),
            }
        )
        
        if not created:
            grade.score = ai_result.get('score', 0)
            grade.comment = ai_result.get('feedback', '')
            grade.ai_graded = True
            grade.ai_confidence = ai_result.get('confidence', 80)
            grade.ai_feedback = ai_result
            grade.ai_strengths = ', '.join(ai_result.get('strengths', []))
            grade.ai_weaknesses = ', '.join(ai_result.get('weaknesses', []))
            grade.ai_suggestions = ', '.join(ai_result.get('recommendations', []))
            grade.save()
        
        # Обновляем статус ответа
        submission.status = 'checked'
        submission.save()
        
        return JsonResponse({
            'success': True,
            'grade': {
                'score': float(grade.score),
                'comment': grade.comment,
                'ai_graded': grade.ai_graded,
                'ai_confidence': grade.ai_confidence,
                'ai_feedback': grade.ai_feedback,
                'ai_strengths': grade.ai_strengths,
                'ai_weaknesses': grade.ai_weaknesses,
                'ai_suggestions': grade.ai_suggestions,
            }
        })
        
    except Exception as e:
        print(f"AI check error: {e}")
        return JsonResponse({'error': f'Внутренняя ошибка: {str(e)}'}, status=500)


@login_required
@mentor_required
def ai_analyze_class(request, course_id):
    """AI анализ всего класса"""
    course = get_mentor_course(request.user, course_id)
    
    try:
        # Собираем данные по всем студентам курса
        students_data = []
        course_students = CourseStudent.objects.filter(
            course=course, status='active'
        ).select_related('student')
        
        for cs in course_students:
            student_data = {
                'name': cs.student.full_name or cs.student.user.username,
                'email': cs.student.user.email,
                'enrollment_date': cs.enrolled_at.isoformat() if cs.enrolled_at else None,
                'assignments_stats': {
                    'total': Assignment.objects.filter(course=course).count(),
                    'submitted': AssignmentSubmission.objects.filter(
                        assignment__course=course, 
                        student=cs.student, 
                        status='submitted'
                    ).count(),
                    'graded': AssignmentGrade.objects.filter(
                        submission__assignment__course=course,
                        submission__student=cs.student
                    ).count(),
                }
            }
            
            # Добавляем оценки
            grades = AssignmentGrade.objects.filter(
                submission__assignment__course=course,
                submission__student=cs.student
            )
            if grades:
                scores = [float(g.score) for g in grades]
                student_data['assignments_stats']['avg_score'] = sum(scores) / len(scores)
                student_data['assignments_stats']['max_score'] = max(scores)
                student_data['assignments_stats']['min_score'] = min(scores)
            else:
                student_data['assignments_stats']['avg_score'] = 0
                student_data['assignments_stats']['max_score'] = 0
                student_data['assignments_stats']['min_score'] = 0
            
            students_data.append(student_data)
        
        # Данные курса
        course_data = {
            'title': course.title,
            'description': course.description,
            'mentor': course.mentor.full_name or course.mentor.username if course.mentor else 'No mentor',
            'total_students': len(students_data),
            'students': students_data
        }
        
        # Вызываем AI для анализа
        ai_analysis = nvidia_ai_service.analyze_dashboard(course_data)
        
        if 'error' in ai_analysis:
            return JsonResponse({'error': f'AI ошибка: {ai_analysis["error"]}'}, status=500)
        
        return JsonResponse({
            'success': True,
            'analysis': ai_analysis,
            'course_data': course_data
        })
        
    except Exception as e:
        print(f"AI analysis error: {e}")
        return JsonResponse({'error': f'Внутренняя ошибка: {str(e)}'}, status=500)
