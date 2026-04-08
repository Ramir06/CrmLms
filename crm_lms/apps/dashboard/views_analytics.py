from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from apps.core.mixins import admin_required
from apps.students.models import Student
from apps.courses.models import Course, CourseStudent
from apps.attendance.models import AttendanceRecord


@login_required
@admin_required
def analytics_dashboard(request):
    """Дашборд аналитики с графиками посещаемости и распределением студентов"""
    
    # Посещаемость за последние 30 дней
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Получаем данные о посещаемости
    attendance_data = []
    for i in range(30):
        date = (timezone.now() - timedelta(days=i)).date()
        present_count = AttendanceRecord.objects.filter(
            lesson__lesson_date=date,
            status='present'
        ).count()
        absent_count = AttendanceRecord.objects.filter(
            lesson__lesson_date=date,
            status='absent'
        ).count()
        
        attendance_data.append({
            'date': date.strftime('%d.%m'),
            'present': present_count,
            'absent': absent_count
        })
    
    attendance_data.reverse()  # Чтобы даты шли в хронологическом порядке
    
    # Распределение студентов по курсам
    courses_data = []
    courses = Course.objects.filter(is_archived=False).annotate(
        student_count=Count('course_students')
    ).order_by('-student_count')
    
    # Генерируем цвета для курсов
    colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
    ]
    
    for i, course in enumerate(courses):
        courses_data.append({
            'id': course.id,
            'title': course.title,
            'student_count': course.student_count,
            'color': colors[i % len(colors)]
        })
    
    # Общая статистика
    total_students = Student.objects.count()
    total_active_students = Student.objects.filter(status='active').count()
    total_courses = Course.objects.filter(is_archived=False).count()
    
    # Топ-5 самых посещаемых курсов
    top_courses = courses[:5]
    
    context = {
        'attendance_data': attendance_data,
        'courses_data': courses_data,
        'total_students': total_students,
        'total_active_students': total_active_students,
        'total_courses': total_courses,
        'top_courses': top_courses,
        'page_title': 'Аналитика',
        'active_menu': 'analytics'
    }
    
    return render(request, 'admin/analytics/dashboard.html', context)


def course_students_detail(request, course_id):
    """Детальная информация о студентах курса"""
    course = get_object_or_404(Course, pk=course_id)
    
    students = CourseStudent.objects.filter(
        course=course
    ).select_related('student').order_by('-joined_at')
    
    context = {
        'course': course,
        'students': students,
        'page_title': f'Студенты курса - {course.title}',
        'active_menu': 'analytics'
    }
    
    return render(request, 'admin/analytics/course_students.html', context)
