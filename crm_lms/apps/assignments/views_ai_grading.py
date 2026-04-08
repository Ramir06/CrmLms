from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from apps.assignments.models import Assignment, AssignmentSubmission, AssignmentGrade
from apps.assignments.ai_grading import grade_assignment_with_ai, batch_grade_assignments
from apps.courses.models import Course
from apps.core.mixins import mentor_required

@mentor_required
@login_required
def ai_grading_dashboard(request):
    """Дашборд AI-оценки для ментора"""
    mentor = request.user
    courses = Course.objects.filter(mentor=mentor)
    
    # Получаем непроверенные задания
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__course__in=courses,
        status='submitted'
    ).select_related('assignment', 'assignment__course', 'student')
    
    # Статистика AI-оценки
    ai_graded_count = AssignmentGrade.objects.filter(
        submission__assignment__course__in=courses,
        ai_graded=True
    ).count()
    
    total_graded = AssignmentGrade.objects.filter(
        submission__assignment__course__in=courses
    ).count()
    
    context = {
        'pending_submissions': pending_submissions,
        'courses': courses,
        'ai_graded_count': ai_graded_count,
        'total_graded': total_graded,
        'ai_percentage': (ai_graded_count / total_graded * 100) if total_graded > 0 else 0
    }
    
    return render(request, 'mentor/assignments/ai_grading_dashboard.html', context)

@mentor_required
@login_required
@require_POST
def ai_grade_submission(request, submission_id):
    """AI-оценка конкретного задания"""
    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        assignment__course__mentor=request.user
    )
    
    if submission.status != 'submitted':
        return JsonResponse({
            'success': False,
            'error': f'Задание уже проверено. Статус: {submission.status}'
        })
    
    # Проверяем, есть ли текст ответа
    if not submission.answer_text and not submission.file:
        return JsonResponse({
            'success': False,
            'error': 'Нет текста ответа или файла для оценки'
        })
    
    # AI-оценка
    result = grade_assignment_with_ai(submission.assignment, submission)
    
    if result['success']:
        ai_result = result['ai_result']
        
        # Создаем или обновляем оценку
        grade, created = AssignmentGrade.objects.get_or_create(submission=submission)
        
        grade.score = ai_result['score']
        grade.comment = ai_result.get('detailed_feedback', '')
        grade.ai_graded = True
        grade.ai_confidence = ai_result.get('confidence', 0)
        grade.ai_feedback = ai_result
        grade.ai_strengths = ', '.join(ai_result.get('strengths', []))
        grade.ai_weaknesses = ', '.join(ai_result.get('weaknesses', []))
        grade.ai_suggestions = ', '.join(ai_result.get('suggestions', []))
        grade.plagiarism_suspicious = ai_result.get('plagiarism_check', {}).get('suspicious', False)
        grade.plagiarism_reason = ai_result.get('plagiarism_check', {}).get('reason', '')
        grade.save()
        
        # Обновляем статус submission
        submission.status = 'checked'
        submission.save()
        
        return JsonResponse({
            'success': True,
            'grade': {
                'score': grade.score,
                'comment': grade.comment,
                'confidence': grade.ai_confidence,
                'strengths': grade.ai_strengths,
                'weaknesses': grade.ai_weaknesses,
                'suggestions': grade.ai_suggestions,
                'plagiarism_suspicious': grade.plagiarism_suspicious,
                'max_score': submission.assignment.max_score
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'error': result['error'],
            'raw_response': result.get('raw_response', '')[:500]  # Показываем часть ответа для отладки
        })

@mentor_required
@login_required
@require_POST
def batch_ai_grade(request):
    """Массовая AI-оценка заданий"""
    course_id = request.POST.get('course_id')
    assignment_id = request.POST.get('assignment_id')
    
    if course_id:
        # Все задания курса
        submissions = AssignmentSubmission.objects.filter(
            assignment__course_id=course_id,
            assignment__course__mentor=request.user,
            status='submitted'
        )
    elif assignment_id:
        # Конкретное задание
        submissions = AssignmentSubmission.objects.filter(
            assignment_id=assignment_id,
            assignment__course__mentor=request.user,
            status='submitted'
        )
    else:
        return JsonResponse({
            'success': False,
            'error': 'Не указан курс или задание'
        })
    
    results = batch_grade_assignments(submissions)
    
    successful = len([r for r in results if 'grade' in r])
    failed = len([r for r in results if 'error' in r])
    
    return JsonResponse({
        'success': True,
        'processed': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    })

@mentor_required
@login_required
def ai_grading_review(request, submission_id):
    """Страница проверки AI-оценки"""
    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        assignment__course__mentor=request.user
    )
    
    try:
        grade = submission.grade
    except AssignmentGrade.DoesNotExist:
        grade = None
    
    context = {
        'submission': submission,
        'grade': grade,
        'assignment': submission.assignment
    }
    
    return render(request, 'mentor/assignments/ai_grading_review.html', context)

@mentor_required
@login_required
@require_POST
def override_ai_grade(request, submission_id):
    """Корректировка AI-оценки ментором"""
    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        assignment__course__mentor=request.user
    )
    
    try:
        grade = submission.grade
    except AssignmentGrade.DoesNotExist:
        grade = AssignmentGrade.objects.create(submission=submission)
    
    # Обновляем оценку ментором
    grade.score = request.POST.get('score')
    grade.comment = request.POST.get('comment')
    grade.checked_by = request.user
    grade.ai_graded = False  # Теперь это ручная оценка
    grade.save()
    
    submission.status = 'checked'
    submission.save()
    
    messages.success(request, 'Оценка успешно обновлена')
    return redirect('mentor:ai_grading_dashboard')
