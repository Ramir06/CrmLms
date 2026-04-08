from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
import json
import calendar

from apps.students.models import Student
from apps.courses.models import Course
from apps.mentors.models import MentorProfile
from apps.leads.models import Lead
from apps.payments.models import Payment
from apps.salaries.models import SalaryAccrual
from apps.news.models import News
from apps.notifications.models import Notification
from apps.lessons.models_substitute import MentorSubstitution
from apps.core.mixins import get_menu_position, get_student_form_fields, get_current_organization
from apps.core.ai_service import nvidia_ai_service
from datetime import datetime, timedelta
from .widgets_analytics import get_analytics_widgets


@login_required
def dashboard_index(request):
    if request.user.role in ('admin', 'superadmin'):
        return admin_dashboard(request)
    elif request.user.role == 'manager':
        return redirect('manager:dashboard')
    elif request.user.role == 'mentor':
        return mentor_dashboard(request)
    return redirect('accounts:login')


def admin_dashboard(request):
    # Получаем текущую организацию
    current_org = get_current_organization(request.user)
    
    # Basic counts - фильтруем по организации
    students_queryset = Student.objects.filter(organization=current_org) if current_org else Student.objects.none()
    mentors_queryset = MentorProfile.objects.filter(organization=current_org) if current_org else MentorProfile.objects.none()
    leads_queryset = Lead.objects.filter(organization=current_org) if current_org else Lead.objects.none()
    courses_queryset = Course.objects.filter(organization=current_org) if current_org else Course.objects.none()
    
    students_count = students_queryset.filter(status='active').count()
    mentors_count = mentors_queryset.filter(is_active=True).count()
    leads_count = leads_queryset.filter(is_archived=False).count()
    courses_count = courses_queryset.filter(is_archived=False, status='active').count()
    
    # Tasks today (mock data)
    tasks_today_count = 5
    
    today = timezone.localdate()
    
    # График студентов за последние 6 месяцев
    monthly_students_labels = []
    monthly_students_data = []
    
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_students = students_queryset.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).count()
        
        monthly_students_labels.insert(0, month_start.strftime('%b'))
        monthly_students_data.insert(0, month_students)
    
    # Финансовые данные (упрощенные)
    finance_labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн']
    finance_income_data = [45000, 52000, 48000, 61000, 58000, 67000]
    finance_expense_data = [32000, 35000, 31000, 38000, 36000, 42000]
    
    # Доходы за текущий месяц
    current_month = today.month
    current_year = today.year
    
    try:
        monthly_income = Payment.objects.filter(
            paid_at__month=current_month,
            paid_at__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
    except Exception as e:
        print(f"Error calculating monthly income: {e}")
        monthly_income = 0
    
    # Процент платежей
    total_students = students_queryset.count()
    paying_students = Payment.objects.filter(
        paid_at__month=current_month,
        paid_at__year=current_year
    ).values('student').distinct().count()
    payment_percent = (paying_students / total_students * 100) if total_students > 0 else 0
    
    # Изменение дохода
    income_change_percent = 12.5  # mock data
    
    # Таблица курсов
    courses_table = []
    for course in courses_queryset.filter(is_archived=False)[:10]:
        courses_table.append({
            'course': course,
            'students': course.current_students_count,
            'progress': 0,  # Временно убираем progress, так как его нет в модели Course
            'status': course.status
        })
    
    # Уроки сегодня
    from apps.lessons.models import Lesson
    today_lessons = Lesson.objects.filter(lesson_date=today).count()
    
    # Последние новости
    recent_news = News.objects.filter(is_published=True).order_by('-created_at')[:5]
    
    # Аналитические виджеты
    analytics_widgets = get_analytics_widgets()
    
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
        'today_lessons': today_lessons,
        'recent_news': recent_news,
        'analytics_widgets': analytics_widgets,
        'page_title': 'Дашборд',
        'menu_position': get_menu_position(),
        'student_form_fields': get_student_form_fields(),
        'current_organization': get_current_organization(request.user),
    }
    
    # Добавляем AI анализ дашборда
    dashboard_data = {
        'students_count': students_count,
        'mentors_count': mentors_count,
        'leads_count': leads_count,
        'courses_count': courses_count,
        'monthly_income': monthly_income,
        'monthly_students_labels': monthly_students_labels,
        'monthly_students_data': monthly_students_data,
        'finance_income_data': finance_income_data,
        'finance_expense_data': finance_expense_data,
        'courses_table': [
            {
                'title': course['course'].title,
                'students': course['course'].current_students_count,
                'status': course['course'].status,
                'progress': 0  # Временно убираем progress, так как его нет в модели Course
            }
            for course in courses_table
        ],
        'organization': current_org.name if current_org else 'Все организации'
    }
    
    try:
        ai_analysis = nvidia_ai_service.analyze_dashboard(dashboard_data)
        if 'error' not in ai_analysis:
            context['ai_analysis'] = ai_analysis
        else:
            context['ai_analysis'] = None
            print(f"AI analysis error: {ai_analysis['error']}")
    except Exception as e:
        print(f"AI analysis exception: {e}")
        context['ai_analysis'] = None
    
    return render(request, 'admin/dashboard/index.html', context)


def mentor_dashboard(request):
    from datetime import date
    user = request.user
    today = timezone.localdate()
    current_time = timezone.now().time()
    
    # Основные курсы ментора
    my_courses = Course.objects.filter(mentor=user, is_archived=False).prefetch_related('course_students').order_by('status', 'title')
    
    # Исключаем курсы, где ментор был заменяющим и уже провел урок
    from apps.lessons.models_substitute import CompletedSubstitution
    completed_course_ids = CompletedSubstitution.objects.filter(
        substitute_mentor=user
    ).values_list('course_id', flat=True)
    
    my_courses = my_courses.exclude(id__in=completed_course_ids)
    
    total_students = sum(c.current_students_count for c in my_courses)

    from apps.assignments.models import AssignmentSubmission
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__course__mentor=user, status='submitted'
    ).count()

    from apps.lessons.models import Lesson
    # Уроки основного ментора (без замен)
    today_lessons = Lesson.objects.filter(
        course__mentor=user, 
        lesson_date=today,
        temporary_mentor__isnull=True  # Только уроки без замены
    ).count()

    # Получаем активные замены на сегодня
    from apps.lessons.models_substitute import MentorSubstitution
    substitutions = MentorSubstitution.objects.filter(
        substitute_mentor=user,
        status='confirmed',
        lesson__lesson_date=today
    ).select_related('lesson', 'lesson__course', 'original_mentor')

    # Проверяем, какие уроки еще не начались или идут сейчас
    active_substitutions = []
    for substitution in substitutions:
        lesson = substitution.lesson
        
        # Если урок еще не начался или идет сейчас
        if lesson.start_time >= current_time or lesson.end_time >= current_time:
            active_substitutions.append(substitution)

    # Формируем карточки курсов для замен
    substitute_courses = []
    for substitution in active_substitutions:
        course = substitution.lesson.course
        lesson = substitution.lesson
        
        substitute_courses.append({
            'course': course,
            'lesson': lesson,
            'original_mentor': substitution.original_mentor,
            'start_time': lesson.start_time,
            'end_time': lesson.end_time,
            'classroom': lesson.classroom,
        })
    
    context = {
        'my_courses': my_courses,
        'total_students': total_students,
        'pending_submissions': pending_submissions,
        'today_lessons': today_lessons,
        'substitute_courses': substitute_courses,
        'page_title': 'Дашборд ментора',
        'current_date': date.today(),
    }
    
    return render(request, 'mentor/dashboard/index.html', context)


@login_required
def ai_analyze_dashboard(request):
    """AI анализ дашборда по AJAX"""
    if request.user.role not in ('admin', 'superadmin'):
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    try:
        # Получаем текущую организацию
        current_org = get_current_organization(request.user)
        
        # Собираем данные дашборда
        students_queryset = Student.objects.filter(organization=current_org) if current_org else Student.objects.all()
        mentors_queryset = MentorProfile.objects.filter(organization=current_org) if current_org else MentorProfile.objects.all()
        leads_queryset = Lead.objects.filter(organization=current_org) if current_org else Lead.objects.all()
        courses_queryset = Course.objects.filter(organization=current_org) if current_org else Course.objects.all()
        
        students_count = students_queryset.filter(status='active').count()
        mentors_count = mentors_queryset.filter(is_active=True).count()
        leads_count = leads_queryset.filter(is_archived=False).count()
        courses_count = courses_queryset.filter(is_archived=False, status='active').count()
        
        # Доходы за текущий месяц
        today = timezone.localdate()
        current_month = today.month
        current_year = today.year
        
        try:
            monthly_income = Payment.objects.filter(
                paid_at__month=current_month,
                paid_at__year=current_year
            ).aggregate(total=Sum('amount'))['total'] or 0
        except:
            monthly_income = 0
        
        # Новые лиды и студенты сегодня
        new_leads_today = leads_queryset.filter(created_at__date=today).count()
        new_students_today = students_queryset.filter(created_at__date=today).count()
        
        # Данные по курсам
        courses_data = []
        for course in courses_queryset.filter(is_archived=False, status='active')[:10]:
            courses_data.append({
                'title': course.title,
                'students': course.current_students_count,
                'status': course.status,
                'progress': 0  # Временно убираем progress, так как его нет в модели Course
            })
        
        dashboard_data = {
            'students_count': students_count,
            'mentors_count': mentors_count,
            'leads_count': leads_count,
            'courses_count': courses_count,
            'new_leads_today': new_leads_today,
            'new_students_today': new_students_today,
            'monthly_income': float(monthly_income),
            'courses_table': courses_data,
            'organization': current_org.name if current_org else 'Все организации',
            'date': today.isoformat()
        }
        
        # Вызываем AI для анализа
        ai_analysis = nvidia_ai_service.analyze_dashboard(dashboard_data)
        
        if 'error' in ai_analysis:
            return JsonResponse({'error': f'AI ошибка: {ai_analysis["error"]}'}, status=500)
        
        return JsonResponse({
            'success': True,
            'analysis': ai_analysis,
            'dashboard_data': dashboard_data
        })
        
    except Exception as e:
        print(f"AI analysis error: {e}")
        return JsonResponse({'error': f'Внутренняя ошибка: {str(e)}'}, status=500)
