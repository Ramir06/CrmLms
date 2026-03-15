from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
import json
import calendar

from apps.students.models import Student
from apps.courses.models import Course
from apps.mentors.models import MentorProfile
from apps.leads.models import Lead
from apps.payments.models import Payment
from apps.salaries.models import SalaryAccrual
from apps.news.models import News


@login_required
def dashboard_index(request):
    if request.user.role in ('admin', 'superadmin'):
        return admin_dashboard(request)
    elif request.user.role == 'mentor':
        return mentor_dashboard(request)
    return redirect('accounts:login')


def admin_dashboard(request):
    # Basic counts
    students_count = Student.objects.filter(status='active').count()
    mentors_count = MentorProfile.objects.filter(is_active=True).count()
    leads_count = Lead.objects.filter(is_archived=False).count()
    courses_count = Course.objects.filter(is_archived=False, status='active').count()
    
    # Tasks today (mock data)
    tasks_today_count = 5
    
    # Get current date
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Monthly students data for the last 6 months
    monthly_students_labels = []
    monthly_students_data = []
    
    for i in range(6):
        month = (current_month - i - 1) % 12 + 1
        year = current_year if month <= current_month else current_year - 1
        month_name = calendar.month_name[:3][month-1]
        
        students_in_month = Student.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count()
        
        monthly_students_labels.insert(0, month_name)
        monthly_students_data.insert(0, students_in_month)
    
    # Finance data for the last 6 months
    finance_labels = monthly_students_labels.copy()
    finance_income_data = []
    finance_expense_data = []
    
    for i in range(6):
        month = (current_month - i - 1) % 12 + 1
        year = current_year if month <= current_month else current_year - 1
        
        # Income from payments
        income = Payment.objects.filter(
            paid_at__year=year,
            paid_at__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Expenses (salary accruals)
        expenses = SalaryAccrual.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        finance_income_data.insert(0, float(income))
        finance_expense_data.insert(0, float(expenses))
    
    # Monthly income and payment percent
    monthly_income = Payment.objects.filter(
        paid_at__year=current_year,
        paid_at__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Previous month for comparison
    prev_month = (current_month - 1) % 12 + 1
    prev_year = current_year if prev_month <= current_month else current_year - 1
    
    prev_month_income = Payment.objects.filter(
        paid_at__year=prev_year,
        paid_at__month=prev_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate percentage change
    if prev_month_income > 0:
        income_change_percent = ((monthly_income - prev_month_income) / prev_month_income) * 100
    else:
        income_change_percent = 0
    
    # Payment completion percent (mock data)
    payment_percent = 75
    
    # Recent courses for table
    courses = Course.objects.filter(is_archived=False).select_related('mentor')[:10]
    courses_table = []
    for course in courses:
        income = Payment.objects.filter(course=course).aggregate(s=Sum('amount'))['s'] or 0
        salary = SalaryAccrual.objects.filter(course=course).aggregate(s=Sum('amount'))['s'] or 0
        courses_table.append({
            'course': course,
            'income': income,
            'salary': salary,
            'profit': income - salary,
        })

    recent_news = News.objects.filter(is_published=True)[:3]

    context = {
        'students_count': students_count,
        'mentors_count': mentors_count,
        'leads_count': leads_count,
        'courses_count': courses_count,
        'tasks_today_count': tasks_today_count,
        'monthly_students_labels': json.dumps(monthly_students_labels),
        'monthly_students_data': json.dumps(monthly_students_data),
        'finance_labels': json.dumps(finance_labels),
        'finance_income_data': json.dumps(finance_income_data),
        'finance_expense_data': json.dumps(finance_expense_data),
        'monthly_income': monthly_income,
        'payment_percent': payment_percent,
        'income_change_percent': income_change_percent,
        'courses_table': courses_table,
        'recent_news': recent_news,
        'page_title': 'Дашборд',
    }
    return render(request, 'admin/dashboard/index.html', context)


def mentor_dashboard(request):
    from datetime import date
    user = request.user
    today = timezone.localdate()
    my_courses = Course.objects.filter(mentor=user, is_archived=False).prefetch_related('course_students').order_by('status', 'title')
    total_students = sum(c.current_students_count for c in my_courses)

    from apps.assignments.models import AssignmentSubmission
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__course__mentor=user, status='submitted'
    ).count()

    from apps.lessons.models import Lesson
    today_lessons = Lesson.objects.filter(
        course__mentor=user, lesson_date=today
    ).count()

    recent_news = News.objects.filter(
        is_published=True, audience__in=['all', 'mentors']
    )[:3]

    context = {
        'my_courses': my_courses,
        'my_courses_count': my_courses.count(),
        'total_students': total_students,
        'pending_submissions': pending_submissions,
        'today_lessons': today_lessons,
        'today': today,
        'recent_news': recent_news,
        'page_title': 'Дашборд',
    }
    return render(request, 'mentor/dashboard/index.html', context)
