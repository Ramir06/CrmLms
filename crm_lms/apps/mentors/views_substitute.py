from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.core.mixins import mentor_required
from apps.core.mixins_substitute import SubstituteAccessMixin, check_substitute_access
from apps.mentors.models import MentorProfile
from apps.lessons.models_substitute import MentorSubstitution
from apps.courses.models import Course


class SubstituteCoursesView(SubstituteAccessMixin):
    def get(self, request):
        mentor = request.user
        
        # Получаем подтвержденные замены для ментора
        substitutions = MentorSubstitution.objects.filter(
            substitute_mentor=mentor,
            status='confirmed',
            lesson__lesson_date__gte=timezone.now().date()
        ).select_related(
            'lesson',
            'lesson__course',
            'original_mentor'
        ).order_by('lesson__lesson_date', 'lesson__start_time')
        
        # Группируем по курсам
        courses_with_substitutions = {}
        for substitution in substitutions:
            course = substitution.lesson.course
            if course.id not in courses_with_substitutions:
                courses_with_substitutions[course.id] = {
                    'course': course,
                    'original_mentor': substitution.original_mentor,
                    'substitutions': []
                }
            courses_with_substitutions[course.id]['substitutions'].append(substitution)
        
        context = {
            'courses_with_substitutions': courses_with_substitutions.values(),
            'page_title': 'Мои замены'
        }
        
        return render(request, 'mentors/substitute_courses.html', context)


@login_required
@mentor_required
def substitute_courses_view(request):
    view = SubstituteCoursesView()
    return view.get(request)


@login_required
@mentor_required
def substitute_course_detail_view(request, course_id):
    """Детальная страница курса с заменой"""
    mentor = request.user
    course = get_object_or_404(Course, pk=course_id)
    
    # Проверяем, что у ментора есть подтвержденные замены на этот курс
    substitutions = MentorSubstitution.objects.filter(
        substitute_mentor=mentor,
        status='confirmed',
        lesson__course=course
    ).select_related('lesson')
    
    if not substitutions.exists():
        from django.contrib import messages
        messages.error(request, 'У вас нет доступа к этому курсу')
        return redirect('mentors:substitute_courses')
    
    # Получаем уроки, на которых ментор является заменяющим
    substitute_lessons = [sub.lesson for sub in substitutions]
    
    context = {
        'course': course,
        'substitute_lessons': substitute_lessons,
        'substitutions': substitutions,
        'page_title': f'Замена: {course.title}'
    }
    
    return render(request, 'mentors/substitute_course_detail.html', context)
