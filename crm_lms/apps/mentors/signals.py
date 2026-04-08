from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.attendance.models import AttendanceRecord
from apps.assignments.models import AssignmentGrade
from apps.reviews.models import LessonFeedback
from .kpi_utils import update_mentor_kpi

User = get_user_model()


@receiver(post_save, sender=AttendanceRecord)
def update_kpi_on_attendance_change(sender, instance, created, **kwargs):
    """
    Обновляет KPI ментора при изменении посещаемости
    """
    try:
        # Получаем ментора урока
        mentor = instance.lesson.course.mentor
        if mentor and mentor.role == 'mentor':
            update_mentor_kpi(mentor.id)
    except Exception:
        # Игнорируем ошибки, чтобы не прерывать основной процесс
        pass


@receiver(post_delete, sender=AttendanceRecord)
def update_kpi_on_attendance_delete(sender, instance, **kwargs):
    """
    Обновляет KPI ментора при удалении записи посещаемости
    """
    try:
        mentor = instance.lesson.course.mentor
        if mentor and mentor.role == 'mentor':
            update_mentor_kpi(mentor.id)
    except Exception:
        pass


@receiver(post_save, sender=AssignmentGrade)
def update_kpi_on_grade_change(sender, instance, created, **kwargs):
    """
    Обновляет KPI ментора при изменении оценки
    """
    try:
        # Получаем ментора через задание
        mentor = instance.submission.assignment.course.mentor
        if mentor and mentor.role == 'mentor':
            update_mentor_kpi(mentor.id)
    except Exception:
        pass


@receiver(post_delete, sender=AssignmentGrade)
def update_kpi_on_grade_delete(sender, instance, **kwargs):
    """
    Обновляет KPI ментора при удалении оценки
    """
    try:
        mentor = instance.submission.assignment.course.mentor
        if mentor and mentor.role == 'mentor':
            update_mentor_kpi(mentor.id)
    except Exception:
        pass


@receiver(post_save, sender=LessonFeedback)
def update_kpi_on_feedback_change(sender, instance, created, **kwargs):
    """
    Обновляет KPI ментора при изменении отзыва
    """
    try:
        # Получаем ментора через урок
        mentor = instance.feedback_link.lesson.course.mentor
        if mentor and mentor.role == 'mentor':
            update_mentor_kpi(mentor.id)
    except Exception:
        pass


@receiver(post_delete, sender=LessonFeedback)
def update_kpi_on_feedback_delete(sender, instance, **kwargs):
    """
    Обновляет KPI ментора при удалении отзыва
    """
    try:
        mentor = instance.feedback_link.lesson.course.mentor
        if mentor and mentor.role == 'mentor':
            update_mentor_kpi(mentor.id)
    except Exception:
        pass
