from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count, Sum

from apps.core.mixins import mentor_required, admin_required
from apps.courses.models import Course, CourseStudent
from apps.lessons.models import Lesson
from apps.attendance.models import AttendanceRecord
from apps.assignments.models import Assignment, AssignmentSubmission, AssignmentGrade


def get_mentor_course(user, course_id):
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def smart_report(request, course_id):
    course = get_mentor_course(request.user, course_id)

    total_students = CourseStudent.objects.filter(course=course, status='active').count()
    total_lessons = Lesson.objects.filter(course=course, status='completed').count()

    # Attendance stats
    records = AttendanceRecord.objects.filter(lesson__course=course)
    total_records = records.count()
    present_records = records.filter(attendance_status='present').count()
    avg_attendance = round(present_records / total_records * 100, 1) if total_records > 0 else 0

    # Assignment stats
    total_assignments = Assignment.objects.filter(course=course).count()
    checked_submissions = AssignmentSubmission.objects.filter(
        assignment__course=course, status='checked'
    ).count()
    avg_score = AssignmentGrade.objects.filter(
        submission__assignment__course=course
    ).aggregate(avg=Avg('score'))['avg'] or 0

    # Best and weak students
    students_with_scores = []
    for cs in CourseStudent.objects.filter(course=course, status='active').select_related('student'):
        student_records = records.filter(student=cs.student)
        student_present = student_records.filter(attendance_status='present').count()
        student_total = student_records.count()
        att_pct = round(student_present / student_total * 100, 1) if student_total > 0 else 0

        score_avg = AssignmentGrade.objects.filter(
            submission__student=cs.student,
            submission__assignment__course=course,
        ).aggregate(avg=Avg('score'))['avg'] or 0

        students_with_scores.append({
            'cs': cs,
            'att_pct': att_pct,
            'avg_score': round(float(score_avg), 1),
        })

    best_students = sorted(students_with_scores, key=lambda x: x['avg_score'], reverse=True)[:5]
    weak_students = sorted(students_with_scores, key=lambda x: x['att_pct'])[:5]

    context = {
        'course': course,
        'total_students': total_students,
        'total_lessons': total_lessons,
        'avg_attendance': avg_attendance,
        'total_assignments': total_assignments,
        'checked_submissions': checked_submissions,
        'avg_score': round(float(avg_score), 1),
        'best_students': best_students,
        'weak_students': weak_students,
        'page_title': 'Смарт-отчёт',
        'active_menu': 'smart_report',
    }
    return render(request, 'mentor/reports/smart_report.html', context)


@login_required
@admin_required
def admin_reports(request):
    from apps.students.models import Student
    from apps.payments.models import Payment
    from apps.salaries.models import SalaryAccrual
    from apps.core.mixins_organization import get_current_organization, filter_by_organization
    from django.utils import timezone

    # Получаем текущую организацию
    current_org = get_current_organization(request.user)
    
    # Фильтруем студентов по организации
    students_qs = Student.objects.filter(status='active')
    students_qs = filter_by_organization(students_qs, current_org)
    total_students = students_qs.count()
    
    # Фильтруем курсы по организации
    courses_qs = Course.objects.filter(is_archived=False)
    courses_qs = filter_by_organization(courses_qs, current_org)
    total_courses = courses_qs.count()
    
    # Фильтруем оплаты по организации (через студентов)
    if current_org:
        total_income = Payment.objects.filter(
            student__organization=current_org,
            paid_at__isnull=False
        ).aggregate(s=Sum('amount'))['s'] or 0
    else:
        total_income = Payment.objects.filter(paid_at__isnull=False).aggregate(s=Sum('amount'))['s'] or 0
    
    # Расчет зарплат за текущий месяц
    current_month = timezone.now().date().replace(day=1)
    if current_org:
        total_salaries = SalaryAccrual.objects.filter(
            month=current_month,
            mentor__mentor_profile__organization=current_org
        ).aggregate(s=Sum('amount'))['s'] or 0
    else:
        total_salaries = SalaryAccrual.objects.filter(
            month=current_month
        ).aggregate(s=Sum('amount'))['s'] or 0
    
    # Расчет прибыли
    profit = total_income - total_salaries
    
    # Данные для сводной таблицы по курсам
    courses_report = []
    for course in courses_qs.select_related('mentor').prefetch_related('course_students'):
        # Студенты на курсе
        students_count = course.course_students.filter(status='active').count()
        
        # Доход по курсу
        if current_org:
            course_income = Payment.objects.filter(
                student__organization=current_org,
                course=course,
                paid_at__isnull=False
            ).aggregate(s=Sum('amount'))['s'] or 0
        else:
            course_income = Payment.objects.filter(
                course=course,
                paid_at__isnull=False
            ).aggregate(s=Sum('amount'))['s'] or 0
        
        # Зарплата по курсу за текущий месяц
        if current_org:
            course_salary = SalaryAccrual.objects.filter(
                course=course,
                month=current_month,
                mentor__mentor_profile__organization=current_org
            ).aggregate(s=Sum('amount'))['s'] or 0
        else:
            course_salary = SalaryAccrual.objects.filter(
                course=course,
                month=current_month
            ).aggregate(s=Sum('amount'))['s'] or 0
        
        # Посещаемость
        total_records = AttendanceRecord.objects.filter(lesson__course=course).count()
        present_records = AttendanceRecord.objects.filter(
            lesson__course=course, 
            attendance_status='present'
        ).count()
        attendance_pct = round(present_records / total_records * 100, 1) if total_records > 0 else 0
        
        courses_report.append({
            'course': course,
            'students': students_count,
            'income': course_income,
            'salary': course_salary,
            'profit': course_income - course_salary,
            'attendance_pct': attendance_pct
        })

    context = {
        'total_students': total_students,
        'total_income': total_income,
        'total_courses': total_courses,
        'total_salaries': total_salaries,
        'profit': profit,
        'courses_report': courses_report,
        'page_title': 'Отчёты',
    }
    return render(request, 'admin/reports/index.html', context)
