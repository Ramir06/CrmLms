from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import JsonResponse

from apps.core.mixins import mentor_required
from apps.courses.models import Course, CourseStudent
from .models import Quiz, Question, Choice, QuizAttempt, AttemptAnswer


def get_mentor_course(user, course_id):
    return get_object_or_404(Course, pk=course_id, mentor=user, is_archived=False)


# ─── Mentor views ────────────────────────────────────────────────────────────

@login_required
@mentor_required
def quiz_list(request, course_id):
    course = get_mentor_course(request.user, course_id)
    quizzes = Quiz.objects.filter(course=course).prefetch_related('questions', 'attempts')
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'quizzes': quizzes,
        'page_title': 'Тесты',
        'active_menu': 'quizzes',
    }
    return render(request, 'mentor/quizzes/list.html', context)


@login_required
@mentor_required
def quiz_create(request, course_id):
    course = get_mentor_course(request.user, course_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        time_limit = int(request.POST.get('time_limit', 0) or 0)
        pass_score = int(request.POST.get('pass_score', 60) or 60)
        create_assignment = request.POST.get('create_assignment') == 'on'
        
        if title:
            quiz = Quiz.objects.create(
                course=course, title=title, description=description,
                time_limit=time_limit, pass_score=pass_score,
            )
            
            # Create linked assignment if requested
            if create_assignment:
                from apps.assignments.models import Assignment
                assignment = Assignment.objects.create(
                    course=course,
                    quiz=quiz,
                    title=title,
                    description=description,
                    max_score=100,  # Default max score for quiz
                    is_required=True,
                    is_visible=True,
                    order=Assignment.objects.filter(course=course).count()
                )
                messages.success(request, f'Тест «{quiz.title}» и связанное задание созданы.')
            else:
                messages.success(request, f'Тест «{quiz.title}» создан.')
            
            return redirect('quizzes:detail', course_id=course_id, quiz_id=quiz.pk)
    
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'page_title': 'Создать тест',
        'active_menu': 'quizzes',
    }
    return render(request, 'mentor/quizzes/quiz_form.html', context)


@login_required
@mentor_required
def quiz_detail(request, course_id, quiz_id):
    course = get_mentor_course(request.user, course_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, course=course)
    questions = quiz.questions.prefetch_related('choices').all()
    attempts = quiz.attempts.select_related('course_student__student').prefetch_related('answers').order_by('-created_at')
    course_students = CourseStudent.objects.filter(course=course, status='active').select_related('student')
    
    # Calculate statistics and correct answers count for each attempt
    passed_attempts = []
    failed_attempts = []
    attempts_with_stats = []
    
    for att in attempts:
        correct_count = sum(1 for answer in att.answers.all() if answer.is_correct)
        att.correct_answers_count = correct_count
        
        if att.passed:
            passed_attempts.append(att)
        elif att.is_submitted:
            failed_attempts.append(att)
        
        attempts_with_stats.append(att)
    
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'quiz': quiz,
        'questions': questions,
        'attempts': attempts_with_stats,
        'passed_attempts': passed_attempts,
        'failed_attempts': failed_attempts,
        'course_students': course_students,
        'page_title': quiz.title,
        'active_menu': 'quizzes',
    }
    return render(request, 'mentor/quizzes/detail.html', context)


@login_required
@mentor_required
def quiz_edit(request, course_id, quiz_id):
    course = get_mentor_course(request.user, course_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, course=course)
    if request.method == 'POST':
        quiz.title = request.POST.get('title', quiz.title).strip()
        quiz.description = request.POST.get('description', quiz.description).strip()
        quiz.time_limit = int(request.POST.get('time_limit', 0) or 0)
        quiz.pass_score = int(request.POST.get('pass_score', 60) or 60)
        quiz.is_active = request.POST.get('is_active') == 'on'
        quiz.save()
        messages.success(request, 'Тест обновлён.')
        return redirect('quizzes:detail', course_id=course_id, quiz_id=quiz.pk)
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'quiz': quiz,
        'page_title': 'Редактировать тест',
        'active_menu': 'quizzes',
    }
    return render(request, 'mentor/quizzes/quiz_form.html', context)


@login_required
@mentor_required
def quiz_delete(request, course_id, quiz_id):
    course = get_mentor_course(request.user, course_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, course=course)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Тест удалён.')
        return redirect('quizzes:list', course_id=course_id)
    return redirect('quizzes:detail', course_id=course_id, quiz_id=quiz_id)


@login_required
@mentor_required
def question_create(request, course_id, quiz_id):
    course = get_mentor_course(request.user, course_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, course=course)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        q_type = request.POST.get('question_type', 'single')
        points = int(request.POST.get('points', 1) or 1)
        choices_texts = request.POST.getlist('choice_text')
        choices_correct = request.POST.getlist('choice_correct')

        if text and choices_texts:
            question = Question.objects.create(
                quiz=quiz, text=text, question_type=q_type, points=points,
                order=quiz.questions.count(),
            )
            for i, ct in enumerate(choices_texts):
                ct = ct.strip()
                if ct:
                    Choice.objects.create(
                        question=question,
                        text=ct,
                        is_correct=str(i) in choices_correct,
                        order=i,
                    )
            messages.success(request, 'Вопрос добавлен.')
            return redirect('quizzes:detail', course_id=course_id, quiz_id=quiz_id)
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'quiz': quiz,
        'page_title': 'Добавить вопрос',
        'active_menu': 'quizzes',
    }
    return render(request, 'mentor/quizzes/question_form.html', context)


@login_required
@mentor_required
def question_delete(request, course_id, quiz_id, question_id):
    course = get_mentor_course(request.user, course_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, course=course)
    question = get_object_or_404(Question, pk=question_id, quiz=quiz)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Вопрос удалён.')
    return redirect('quizzes:detail', course_id=course_id, quiz_id=quiz_id)


@login_required
@mentor_required
def start_attempt(request, course_id, quiz_id):
    """Mentor creates an attempt link for a specific student."""
    course = get_mentor_course(request.user, course_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id, course=course)
    if request.method == 'POST':
        cs_id = request.POST.get('course_student_id')
        cs = get_object_or_404(CourseStudent, pk=cs_id, course=course)
        attempt = QuizAttempt.objects.create(
            quiz=quiz, course_student=cs, max_score=quiz.total_points()
        )
        take_url = request.build_absolute_uri(f'/quizzes/take/{attempt.token}/')
        messages.success(request, f'Ссылка для {cs.student.full_name}: {take_url}')
        return redirect('quizzes:detail', course_id=course_id, quiz_id=quiz_id)
    return redirect('quizzes:detail', course_id=course_id, quiz_id=quiz_id)


# ─── Student quiz-taking (no login required, token-based) ────────────────────

def take_quiz(request, token):
    attempt = get_object_or_404(QuizAttempt, token=token)
    if attempt.is_submitted:
        return redirect('quiz_result', token=token)

    quiz = attempt.quiz
    questions = quiz.questions.prefetch_related('choices').all()

    if request.method == 'POST':
        total_earned = 0
        for question in questions:
            answer, _ = AttemptAnswer.objects.get_or_create(attempt=attempt, question=question)
            answer.selected_choices.clear()
            selected_ids = request.POST.getlist(f'q_{question.pk}')
            selected_choices = Choice.objects.filter(pk__in=selected_ids, question=question)
            answer.selected_choices.set(selected_choices)

            correct_ids = set(question.correct_choices().values_list('pk', flat=True))
            selected_ids_set = set(int(i) for i in selected_ids if i)

            if question.question_type == 'single':
                is_correct = selected_ids_set == correct_ids
                earned = question.points if is_correct else 0
            else:
                if correct_ids:
                    correct_selected = selected_ids_set & correct_ids
                    wrong_selected = selected_ids_set - correct_ids
                    earned = round(question.points * (len(correct_selected) - len(wrong_selected)) / len(correct_ids), 2)
                    earned = max(0, earned)
                    is_correct = earned == question.points
                else:
                    is_correct = False
                    earned = 0

            answer.is_correct = is_correct
            answer.points_earned = earned
            answer.save()
            total_earned += earned

        max_score = quiz.total_points()
        percentage = round((total_earned / max_score * 100) if max_score > 0 else 0, 2)
        attempt.score = total_earned
        attempt.max_score = max_score
        attempt.percentage = percentage
        attempt.passed = percentage >= quiz.pass_score
        attempt.submitted_at = timezone.now()
        attempt.save()
        return redirect('quiz_result', token=token)

    context = {
        'attempt': attempt,
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'mentor/quizzes/take.html', context)


def quiz_result(request, token):
    attempt = get_object_or_404(QuizAttempt, token=token)
    answers = attempt.answers.select_related('question').prefetch_related('selected_choices', 'question__choices').all()
    context = {
        'attempt': attempt,
        'answers': answers,
    }
    return render(request, 'mentor/quizzes/result.html', context)
