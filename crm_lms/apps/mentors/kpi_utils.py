from django.db.models import Avg, Count, Q, F, FloatField, ExpressionWrapper, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal


def calculate_mentor_kpi(mentor_user_id):
    """
    Рассчитывает KPI для ментора на основе:
    1. Посещаемости (attendance) - 35%
    2. Оценок студентов (grades) - 35% 
    3. Отзывов студентов (reviews) - 30%
    
    Возвращает словарь с метриками и итоговым KPI
    """
    from apps.courses.models import Course
    from apps.lessons.models import Lesson
    from apps.attendance.models import AttendanceRecord
    from apps.assignments.models import AssignmentGrade
    from apps.reviews.models import LessonFeedback
    
    # Получаем активные курсы ментора
    active_courses = Course.objects.filter(
        mentor_id=mentor_user_id,
        status='active'
    )
    
    if not active_courses.exists():
        return {
            'attendance': 0,
            'grades': 0,
            'reviews': 0,
            'kpi': 0,
            'status': 'not_recommended'
        }
    
    # 1. Расчёт посещаемости
    attendance_data = calculate_attendance_kpi(active_courses)
    
    # 2. Расчёт оценок
    grades_data = calculate_grades_kpi(active_courses)
    
    # 3. Расчёт отзывов
    reviews_data = calculate_reviews_kpi(active_courses)
    
    # Расчёт итогового KPI
    kpi = (
        attendance_data * 0.35 +
        grades_data * 0.35 +
        reviews_data * 0.30
    )
    
    # Определение статуса
    if kpi >= 85:
        status = 'recommended'
    elif kpi >= 70:
        status = 'good'
    elif kpi >= 55:
        status = 'caution'
    else:
        status = 'not_recommended'
    
    return {
        'attendance': round(attendance_data, 1),
        'grades': round(grades_data, 1),
        'reviews': round(reviews_data, 1),
        'kpi': round(kpi, 1),
        'status': status
    }


def calculate_attendance_kpi(active_courses):
    """Рассчитывает KPI посещаемости (0-100)"""
    from apps.attendance.models import AttendanceRecord
    from apps.lessons.models import Lesson
    
    # Получаем все уроки по активным курсам
    lessons = Lesson.objects.filter(
        course__in=active_courses,
        status='completed'
    )
    
    if not lessons.exists():
        return 0
    
    # Общее количество возможных посещений
    total_possible = AttendanceRecord.objects.filter(
        lesson__in=lessons
    ).count()
    
    if total_possible == 0:
        return 0
    
    # Количество фактических посещений (present + late + excused считаем как присутствие)
    total_attended = AttendanceRecord.objects.filter(
        lesson__in=lessons,
        attendance_status__in=['present', 'late', 'excused']
    ).count()
    
    attendance_rate = (total_attended / total_possible) * 100
    return min(attendance_rate, 100)


def calculate_grades_kpi(active_courses):
    """Рассчитывает KPI оценок студентов (0-100)"""
    from apps.assignments.models import AssignmentGrade, AssignmentSubmission
    from apps.students.models import Student
    
    # Получаем все оценки по курсам ментора
    grades = AssignmentGrade.objects.filter(
        submission__assignment__course__in=active_courses
    ).aggregate(
        avg_score=Coalesce(Avg('score'), Decimal('0'), output_field=FloatField())
    )
    
    # Оценки уже в шкале 0-100, просто возвращаем среднее
    return float(grades['avg_score'])


def calculate_reviews_kpi(active_courses):
    """Рассчитывает KPI отзывов студентов (0-100)"""
    from apps.reviews.models import LessonFeedback
    from apps.lessons.models import Lesson
    
    # Получаем уроки по активным курсам
    lessons = Lesson.objects.filter(
        course__in=active_courses,
        status='completed'
    )
    
    if not lessons.exists():
        return 0
    
    # Получаем отзывы по урокам
    reviews = LessonFeedback.objects.filter(
        feedback_link__lesson__in=lessons
    ).aggregate(
        avg_rating=Coalesce(Avg('mentor_rating'), Decimal('0'), output_field=FloatField())
    )
    
    # Конвертируем оценку 1-5 в шкалу 0-100
    if reviews['avg_rating']:
        reviews_kpi = (float(reviews['avg_rating']) / 5) * 100
        return min(reviews_kpi, 100)
    
    return 0


def update_mentor_kpi(mentor_user_id):
    """
    Обновляет KPI ментора в базе данных
    """
    from apps.mentors.models import MentorProfile
    
    try:
        mentor_profile = MentorProfile.objects.get(user_id=mentor_user_id)
        kpi_data = calculate_mentor_kpi(mentor_user_id)
        
        mentor_profile.kpi = kpi_data['kpi']
        mentor_profile.kpi_status = kpi_data['status']
        mentor_profile.kpi_updated_at = timezone.now()
        mentor_profile.save(update_fields=['kpi', 'kpi_status', 'kpi_updated_at'])
        
        return kpi_data
    except MentorProfile.DoesNotExist:
        return None


def get_kpi_status_display(status):
    """Возвращает человекочитаемое отображение статуса KPI"""
    status_map = {
        'recommended': 'Рекомендуется',
        'good': 'Хорошо',
        'caution': 'С осторожностью',
        'not_recommended': 'Не рекомендуется'
    }
    return status_map.get(status, 'Не определён')


def get_kpi_status_color(status):
    """Возвращает цвет для отображения статуса KPI"""
    color_map = {
        'recommended': '#10b981',  # green
        'good': '#3b82f6',        # blue
        'caution': '#f59e0b',      # yellow
        'not_recommended': '#ef4444'  # red
    }
    return color_map.get(status, '#6b7280')  # gray default
