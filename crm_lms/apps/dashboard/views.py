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
    # Получаем параметр организации из URL
    org_id = request.GET.get('org')
    selected_org = None
    user_current_org = get_current_organization(request.user)
    
    if org_id == 'current':
        # Показываем текущую организацию пользователя
        selected_org = user_current_org
    elif org_id == 'all':
        # Явно указано "все организации"
        selected_org = None
    elif org_id and org_id.isdigit():
        # Указан конкретный ID организации
        try:
            from apps.organizations.models import Organization
            selected_org = Organization.objects.get(id=int(org_id))
        except (Organization.DoesNotExist, ValueError):
            selected_org = None
    else:
        # Нет параметра - по умолчанию показываем текущую организацию
        selected_org = user_current_org
    
    # Basic counts - фильтруем по организации
    students_queryset = Student.objects.filter(organization=selected_org) if selected_org else Student.objects.all()
    mentors_queryset = MentorProfile.objects.filter(organization=selected_org) if selected_org else MentorProfile.objects.all()
    leads_queryset = Lead.objects.filter(organization=selected_org) if selected_org else Lead.objects.all()
    courses_queryset = Course.objects.filter(organization=selected_org) if selected_org else Course.objects.all()
    
    students_count = students_queryset.filter(status='active').count()
    mentors_count = mentors_queryset.filter(is_active=True).count()
    leads_count = leads_queryset.filter(is_archived=False).count()
    courses_count = courses_queryset.filter(is_archived=False, status='active').count()
    
    # Tasks today (mock data)
    tasks_today_count = 5
    
    # Get current date
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Monthly students data for the last 6 months
    monthly_students_labels = []
    monthly_students_data = []
    
    print(f"=== DEBUG: Статистика студентов по месяцам ===")
    print(f"Текущая организация: {selected_org}")
    print(f"Всего студентов в организации: {students_queryset.count()}")
    
    for i in range(6):
        month = (current_month - i - 1) % 12 + 1
        year = current_year if month <= current_month else current_year - 1
        # Get month name safely
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_name = month_names[month - 1]
        
        print(f"Проверяем месяц: {month_name} {year}")
        
        students_in_month = students_queryset.filter(
            created_at__year=year,
            created_at__month=month
        ).count()
        
        print(f"  Найдено студентов: {students_in_month}")
        
        monthly_students_labels.insert(0, month_name)
        monthly_students_data.insert(0, students_in_month)
    
    print(f"Итоговые данные: {monthly_students_labels} - {monthly_students_data}")
    print(f"=== END DEBUG ===")
    
    # Finance data for the last 6 months
    finance_labels = monthly_students_labels.copy()
    finance_income_data = []
    finance_expense_data = []
    
    for i in range(6):
        month = (current_month - i - 1) % 12 + 1
        year = current_year if month <= current_month else current_year - 1
        
        # Income from payments - фильтруем по студентам текущей организации
        income = Payment.objects.filter(
            student__in=students_queryset,
            paid_at__year=year,
            paid_at__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Expenses (salary accruals) - TODO: добавить организацию к зарплатам
        expenses = SalaryAccrual.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        finance_income_data.insert(0, float(income))
        finance_expense_data.insert(0, float(expenses))
    
    # Monthly income and payment percent - фильтруем по студентам текущей организации
    monthly_income = Payment.objects.filter(
        student__in=students_queryset,
        paid_at__year=current_year,
        paid_at__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Previous month for comparison
    prev_month = (current_month - 1) % 12 + 1
    prev_year = current_year if prev_month <= current_month else current_year - 1
    
    prev_month_income = Payment.objects.filter(
        student__in=students_queryset,
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
    
    # Recent courses for table - фильтруем по организации
    courses = courses_queryset.filter(is_archived=False).select_related('mentor')[:10]
    courses_table = []
    for course in courses:
        income = Payment.objects.filter(
            course=course,
            student__in=students_queryset
        ).aggregate(s=Sum('amount'))['s'] or 0
        salary = SalaryAccrual.objects.filter(course=course).aggregate(s=Sum('amount'))['s'] or 0
        courses_table.append({
            'course': course,
            'income': income,
            'salary': salary,
            'profit': income - salary,
        })

    # Today's lessons for admin - фильтруем по организации
    from apps.lessons.models import Lesson
    today = timezone.now().date()
    today_lessons = Lesson.objects.filter(
        organization=selected_org,
        lesson_date=today
    ).select_related('course', 'course__mentor', 'temporary_mentor').order_by('start_time') if selected_org else Lesson.objects.none()

    recent_news = News.objects.filter(is_published=True)[:3]  # TODO: добавить организацию к новостям

    # Получаем виджеты аналитики с фильтрацией по организации
    analytics_widgets = get_analytics_widgets(selected_org)
    
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
        'current_organization': selected_org,
        'selected_org': selected_org,
        'user_current_organization': user_current_org,
    }
    
    # Добавляем AI анализ дашборда
    dashboard_data = {
        'students_count': students_count,
        'mentors_count': mentors_count,
        'leads_count': leads_count,
        'courses_count': courses_count,
        'new_leads_today': 0,
        'new_students_today': 0,
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
        'organization': selected_org.name if selected_org else 'Все организации'
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
        
        # Проверяем доступность курса (не добавляем дубликаты)
        if not any(sc['course'].id == course.id for sc in substitute_courses):
            substitute_courses.append({
                'course': course,
                'substitution': substitution,
                'lesson': lesson,
                'original_mentor': substitution.original_mentor,
            })

    recent_news = News.objects.filter(
        is_published=True, audience__in=['all', 'mentors']
    )[:3]

    # Notifications
    recent_notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:3]
    
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    # Debug info
    print(f"DEBUG: Mentor {user.username} - Courses: {my_courses.count()}, Students: {total_students}, Pending: {pending_submissions}, Lessons: {today_lessons}, Substitutions: {len(active_substitutions)}")
    
    # Общее количество уроков сегодня с учетом замен
    total_today_lessons = today_lessons + len(active_substitutions)

    context = {
        'my_courses': my_courses,
        'my_courses_count': my_courses.count(),
        'total_students': total_students,
        'pending_submissions': pending_submissions,
        'today_lessons': today_lessons,
        'total_today_lessons': total_today_lessons,
        'today': today,
        'substitute_courses': substitute_courses,
        'substitute_courses_count': len(substitute_courses),
        'recent_news': recent_news,
        'recent_notifications': recent_notifications,
        'unread_count': unread_count,
        'page_title': 'Дашборд',
        'current_organization': get_current_organization(request.user),
    }
    return render(request, 'mentor/dashboard/index.html', context)


def manager_dashboard(request):
    """Дашборд для менеджеров"""
    from datetime import date
    user = request.user
    today = timezone.localdate()
    
    # Получаем текущую организацию
    current_org = get_current_organization(request.user)
    
    # Если нет организации, показываем дашборд с сообщением
    if not current_org:
        context = {
            'students_count': 0,
            'mentors_count': 0,
            'leads_count': 0,
            'courses_count': 0,
            'new_leads_today': 0,
            'new_students_today': 0,
            'active_courses': [],
            'monthly_income': 0,
            'recent_news': [],
            'recent_notifications': [],
            'unread_count': 0,
            'page_title': 'Дашборд менеджера',
            'current_organization': None,
            'no_organization': True,  # Флаг для шаблона
        }
        return render(request, 'manager/dashboard/index.html', context)


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
    new_students_today = students_queryset.filter(
        status='active',
        created_at__date=today
    ).count()
    
    # Активные курсы
    active_courses = courses_queryset.filter(is_archived=False, status='active')[:5]
    
    # Последние новости
    recent_news = News.objects.filter(is_published=True).order_by('-created_at')[:5]
    
    # Последние уведомления
    recent_notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:5]
    
    # Непрочитанные уведомления
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Доходы за текущий месяц
    from django.db.models import Sum
    current_month = today.month
    current_year = today.year
    
    # Временно упрощаем - берем все платежи без фильтрации по организации
    try:
        monthly_income = Payment.objects.filter(
            paid_at__month=current_month,
            paid_at__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
    except Exception as e:
        print(f"Error calculating monthly income: {e}")
        monthly_income = 0
    
    context = {
        'students_count': students_count,
        'mentors_count': mentors_count,
        'leads_count': leads_count,
        'courses_count': courses_count,
        'new_leads_today': new_leads_today,
        'new_students_today': new_students_today,
        'active_courses': active_courses,
        'monthly_income': monthly_income,
        'recent_news': recent_news,
        'recent_notifications': recent_notifications,
        'unread_count': unread_count,
        'page_title': 'Дашборд менеджера',
        'current_organization': current_org,
        'no_organization': False,
    }
    
    return render(request, 'manager/dashboard/index.html', context)


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
