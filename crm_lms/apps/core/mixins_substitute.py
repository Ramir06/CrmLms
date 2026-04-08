from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from apps.lessons.models_substitute import MentorSubstitution, SubstituteAccess
from datetime import datetime, date


class SubstituteAccessMixin:
    """
    Mixin для проверки прав доступа заменяющего ментора
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Проверяем, является ли пользователь заменяющим ментором
        if not self.is_substitute_mentor(request.user):
            messages.error(request, 'У вас нет прав доступа к этому разделу')
            return redirect('dashboard:index')
        
        return super().dispatch(request, *args, **kwargs)
    
    def is_substitute_mentor(self, user):
        """Проверяем, есть ли у пользователя подтвержденные замены"""
        return MentorSubstitution.objects.filter(
            substitute_mentor=user,
            status='confirmed',
            lesson__lesson_date__gte=date.today()
        ).exists()
    
    def get_substitute_context(self, user):
        """Получаем контекст для заменяющего ментора"""
        substitutions = MentorSubstitution.objects.filter(
            substitute_mentor=user,
            status='confirmed',
            lesson__lesson_date__gte=date.today()
        ).select_related('lesson', 'lesson__course', 'original_mentor')
        
        courses = {}
        for sub in substitutions:
            if sub.lesson.course.id not in courses:
                courses[sub.lesson.course.id] = {
                    'course': sub.lesson.course,
                    'substitutions': [],
                    'original_mentor': sub.original_mentor
                }
            courses[sub.lesson.course.id]['substitutions'].append(sub)
        
        return courses


def check_substitute_access(user, course_id, lesson_date=None):
    """
    Проверяет, имеет ли ментор доступ к курсу как заменяющий
    """
    if user.role != 'mentor':
        return False
    
    queryset = MentorSubstitution.objects.filter(
        substitute_mentor=user,
        status='confirmed',
        lesson__course_id=course_id
    )
    
    if lesson_date:
        queryset = queryset.filter(lesson__lesson_date=lesson_date)
    
    return queryset.exists()


def can_mark_attendance(user, lesson_id):
    """
    Проверяет, может ли ментор отмечать посещаемость для урока
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Checking attendance rights for user {user.username} ({user.role}) on lesson {lesson_id}")
    
    if user.role == 'mentor':
        # Основной ментор курса может отмечать посещаемость
        from apps.lessons.models import Lesson
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
            logger.info(f"Lesson found: {lesson.title}, course: {lesson.course.title}, mentor: {lesson.course.mentor.username if lesson.course.mentor else 'None'}")
            
            if lesson.course.mentor == user:
                logger.info(f"User {user.username} is the main mentor - can mark attendance")
                return True
            else:
                logger.info(f"User {user.username} is not the main mentor")
        except Lesson.DoesNotExist:
            logger.error(f"Lesson {lesson_id} does not exist")
            return False
    
    # Заменяющий ментор может отмечать посещаемость только для своих замен
    substitution_exists = MentorSubstitution.objects.filter(
        substitute_mentor=user,
        lesson_id=lesson_id,
        status='confirmed'
    ).exists()
    
    logger.info(f"Substitution exists for user {user.username}: {substitution_exists}")
    return substitution_exists


def can_create_materials(user, course_id):
    """
    Проверяет, может ли ментор создавать материалы для курса
    """
    if user.role == 'mentor':
        # Основной ментор курса может создавать материалы
        from apps.courses.models import Course
        try:
            course = Course.objects.get(pk=course_id)
            if course.mentor == user:
                return True
        except Course.DoesNotExist:
            return False
    
    # Заменяющий ментор может создавать материалы для курсов, где он заменяет
    return MentorSubstitution.objects.filter(
        substitute_mentor=user,
        lesson__course_id=course_id,
        status='confirmed'
    ).exists()


def can_view_grades(user, course_id):
    """
    Проверяет, может ли ментор просматривать оценки за курс
    """
    if user.role == 'mentor':
        # Основной ментор курса может просматривать оценки
        from apps.courses.models import Course
        try:
            course = Course.objects.get(pk=course_id)
            if course.mentor == user:
                return True
        except Course.DoesNotExist:
            return False
    
    # Заменяющий ментор может просматривать оценки для курсов, где он заменяет
    return MentorSubstitution.objects.filter(
        substitute_mentor=user,
        lesson__course_id=course_id,
        status='confirmed'
    ).exists()


def can_edit_grades(user, course_id):
    """
    Проверяет, может ли ментор редактировать оценки за курс
    """
    if user.role == 'mentor':
        # Основной ментор курса может редактировать оценки
        from apps.courses.models import Course
        try:
            course = Course.objects.get(pk=course_id)
            if course.mentor == user:
                return True
        except Course.DoesNotExist:
            return False
    
    # Заменяющий ментор НЕ может редактировать оценки
    return False
