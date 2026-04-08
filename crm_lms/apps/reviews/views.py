from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Avg
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

from apps.core.mixins import mentor_required
from apps.core.mixins_substitute import check_substitute_access
from apps.courses.models import Course
from apps.lessons.models import Lesson
from apps.lessons.models_substitute import MentorSubstitution
from .models import Review, LessonFeedbackLink, LessonFeedback


from django import forms


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['student', 'type', 'content', 'rating']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            from apps.students.models import Student
            from apps.courses.models import CourseStudent
            student_ids = CourseStudent.objects.filter(course=course, status='active').values_list('student_id', flat=True)
            self.fields['student'].queryset = Student.objects.filter(pk__in=student_ids)


def get_mentor_course_with_substitute_access(user, course_id):
    """
    Получение курса с проверкой прав доступа для заменяющего ментора
    """
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    
    # Проверяем, является ли пользователем основным ментором
    course = get_object_or_404(Course, pk=course_id)
    if course.mentor == user:
        return course
    
    # Проверяем, является ли пользователем заменяющим ментором
    if check_substitute_access(user, course_id):
        return course
    
    raise PermissionDenied("У вас нет прав доступа к этому курсу")


def get_mentor_course(user, course_id):
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def reviews_list(request, course_id):
    """Mentor feedback dashboard: shows aggregated stats + list of lessons with feedback links."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)

    lessons = Lesson.objects.filter(course=course).exclude(status='cancelled').order_by('lesson_date', 'start_time')
    
    # Для заменяющего ментора показываем только уроки, на которые он назначен
    if course.mentor != request.user and request.user.role == 'mentor':
        from datetime import datetime
        substitute_lesson_ids = MentorSubstitution.objects.filter(
            substitute_mentor=request.user,
            status='confirmed',
            lesson__course=course
        ).values_list('lesson_id', flat=True)
        lessons = lessons.filter(id__in=substitute_lesson_ids)

    # Preload feedback links
    links = LessonFeedbackLink.objects.filter(lesson__in=lessons).select_related('lesson')
    link_map = {lnk.lesson_id: lnk for lnk in links}

    # Build lesson rows with link info and response count
    lesson_rows = []
    for lesson in lessons:
        lnk = link_map.get(lesson.pk)
        count = lnk.responses.count() if lnk else 0
        lesson_rows.append({
            'lesson': lesson,
            'link': lnk,
            'response_count': count,
        })

    # Aggregated feedback across all lessons in the course
    all_feedback = LessonFeedback.objects.filter(
        feedback_link__lesson__course=course
    )
    agg = all_feedback.aggregate(
        avg_mentor=Avg('mentor_rating'),
        avg_activity=Avg('self_activity'),
        avg_mood=Avg('mood'),
    )
    total_responses = all_feedback.count()

    # Определяем, является ли пользователь заменяющим ментором
    is_substitute_mentor = course.mentor != request.user and request.user.role == 'mentor'

    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'lesson_rows': lesson_rows,
        'avg_mentor': round(agg['avg_mentor'], 1) if agg['avg_mentor'] else None,
        'avg_activity': round(agg['avg_activity'], 1) if agg['avg_activity'] else None,
        'avg_mood': round(agg['avg_mood'], 1) if agg['avg_mood'] else None,
        'total_responses': total_responses,
        'is_substitute_mentor': is_substitute_mentor,
        'page_title': 'Отзывы',
        'active_menu': 'reviews',
    }
    return render(request, 'mentor/reviews/list.html', context)


@login_required
@mentor_required
@require_POST
def generate_feedback_link(request, course_id, lesson_id):
    """Generate (or return existing) feedback link for a lesson."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    
    # Для заменяющего ментора проверяем, что он назначен на этот урок
    if course.mentor != request.user and request.user.role == 'mentor':
        from apps.core.mixins_substitute import can_mark_attendance
        if not can_mark_attendance(request.user, lesson_id):
            return JsonResponse({'error': 'Вы можете генерировать ссылки только для уроков, на которые назначены'}, status=403)

    link, created = LessonFeedbackLink.objects.get_or_create(lesson=lesson)
    return JsonResponse({
        'ok': True,
        'token': str(link.token),
        'created': created,
    })


@login_required
@mentor_required
def feedback_detail(request, course_id, lesson_id):
    """Mentor view: details of feedback for a specific lesson."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    link = get_object_or_404(LessonFeedbackLink, lesson=lesson)
    responses = link.responses.all().order_by('-created_at')
    agg = responses.aggregate(
        avg_mentor=Avg('mentor_rating'),
        avg_activity=Avg('self_activity'),
        avg_mood=Avg('mood'),
    )
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'lesson': lesson,
        'link': link,
        'responses': responses,
        'avg_mentor': round(agg['avg_mentor'], 1) if agg['avg_mentor'] else None,
        'avg_activity': round(agg['avg_activity'], 1) if agg['avg_activity'] else None,
        'avg_mood': round(agg['avg_mood'], 1) if agg['avg_mood'] else None,
        'page_title': f'Отзывы — Урок {lesson.lesson_date}',
        'active_menu': 'reviews',
    }
    return render(request, 'mentor/reviews/detail.html', context)


def feedback_form(request, token):
    """Public feedback form (no login required). Students rate the lesson."""
    link = get_object_or_404(LessonFeedbackLink, token=token, is_active=True)
    lesson = link.lesson
    submitted = False

    if request.method == 'POST':
        try:
            mentor_rating = int(request.POST.get('mentor_rating', 0))
            self_activity = int(request.POST.get('self_activity', 0))
            mood = int(request.POST.get('mood', 0))
            student_name = request.POST.get('student_name', '').strip()
            comment = request.POST.get('comment', '').strip()

            if all(1 <= v <= 5 for v in [mentor_rating, self_activity, mood]):
                LessonFeedback.objects.create(
                    feedback_link=link,
                    student_name=student_name,
                    mentor_rating=mentor_rating,
                    self_activity=self_activity,
                    mood=mood,
                    comment=comment,
                )
                submitted = True
        except (ValueError, TypeError):
            pass

    context = {
        'link': link,
        'lesson': lesson,
        'course': lesson.course,
        'submitted': submitted,
    }
    return render(request, 'reviews/feedback_form.html', context)
