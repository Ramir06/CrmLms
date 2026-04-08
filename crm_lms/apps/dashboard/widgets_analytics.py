from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.students.models import Student
from apps.courses.models import Course, CourseStudent
from apps.attendance.models import AttendanceRecord


def get_attendance_widget(current_org=None):
    """Виджет посещаемости за последние 7 дней"""
    attendance_data = []
    for i in range(7):
        date = (timezone.now() - timedelta(days=i)).date()
        # Фильтруем по организации
        attendance_filter = {}
        if current_org:
            attendance_filter['lesson__organization'] = current_org
            
        present_count = AttendanceRecord.objects.filter(
            lesson__lesson_date=date,
            attendance_status='present',
            **attendance_filter
        ).count()
        absent_count = AttendanceRecord.objects.filter(
            lesson__lesson_date=date,
            attendance_status='absent',
            **attendance_filter
        ).count()
        
        attendance_data.append({
            'date': date.strftime('%d.%m'),
            'present': present_count,
            'absent': absent_count
        })
    
    attendance_data.reverse()
    
    return {
        'title': 'Посещаемость за 7 дней',
        'type': 'chart',
        'data': attendance_data,
        'icon': 'fas fa-chart-line',
        'color': 'primary'
    }


def get_courses_distribution_widget(current_org=None):
    """Виджет распределения студентов по курсам"""
    courses_data = []
    # Фильтруем по организации
    courses_filter = {}
    if current_org:
        courses_filter['organization'] = current_org
        
    courses = Course.objects.annotate(
        student_count=Count('course_students')
    ).filter(**courses_filter).order_by('-student_count')[:5]
    
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
    
    for i, course in enumerate(courses):
        if course.student_count > 0:  # Только курсы со студентами
            courses_data.append({
                'title': course.title,
                'student_count': course.student_count,
                'color': colors[i % len(colors)],
                'url': f'/analytics/course/{course.id}/students/'
            })
    
    return {
        'title': 'Распределение студентов по курсам',
        'type': 'pie_chart',
        'data': courses_data,
        'icon': 'fas fa-chart-pie',
        'color': 'success'
    }


def get_students_by_months_widget(current_org=None):
    """Виджет новых студентов по месяцам"""
    print(f"=== DEBUG: get_students_by_months_widget ===")
    print(f"current_org: {current_org}")
    
    # Получаем данные за последние 6 месяцев
    students_by_month = []
    current_date = timezone.now()
    
    for i in range(6):
        month = (current_date.month - i - 1) % 12 + 1
        year = current_date.year if month <= current_date.month else current_date.year - 1
        
        print(f"Проверяем месяц: {month} год: {year}")
        
        # Фильтруем по организации
        students_filter = {
            'created_at__year': year,
            'created_at__month': month
        }
        if current_org:
            students_filter['organization'] = current_org
            
        students_count = Student.objects.filter(**students_filter).count()
        
        print(f"  Найдено студентов: {students_count}")
        
        # Получаем название месяца
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_name = month_names[month - 1]
        
        students_by_month.append({
            'month': month_name,
            'count': students_count
        })
    
    students_by_month.reverse()
    print(f"Итоговые данные: {students_by_month}")
    print(f"=== END DEBUG ===")
    
    return {
        'title': 'Новые студенты по месяцам',
        'type': 'bar_chart',
        'data': students_by_month,
        'icon': 'fas fa-user-plus',
        'color': 'info'
    }


def get_top_students_widget(current_org=None):
    """Виджет лучших студентов месяца"""
    from datetime import datetime
    from apps.assignments.models import AssignmentSubmission
    from apps.courses.models import CourseStudent
    
    # Получаем начало текущего месяца
    current_date = timezone.now()
    month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    top_students = []
    
    # Фильтруем по организации
    students_filter = {}
    if current_org:
        students_filter['student__organization'] = current_org
    
    # Получаем всех активных студентов
    course_students = CourseStudent.objects.filter(
        status='active',
        **students_filter
    ).select_related('student', 'course')
    
    for course_student in course_students:
        student = course_student.student
        course = course_student.course
        
        # 1. Считаем оценки за месяц
        submissions = AssignmentSubmission.objects.filter(
            assignment__course=course,
            student=student,
            submitted_at__gte=month_start,
            status='graded',
            grade__isnull=False
        ).select_related('assignment')
        
        total_score = 0
        total_max_score = 0
        for submission in submissions:
            if submission.grade is not None and submission.assignment.max_score is not None:
                total_score += submission.grade
                total_max_score += submission.assignment.max_score
        
        # Рассчитываем средний процент оценок
        grade_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
        
        # 2. Считаем посещаемость за месяц
        attendance_records = AttendanceRecord.objects.filter(
            lesson__course=course,
            student=student,
            lesson__lesson_date__gte=month_start
        )
        
        total_lessons = attendance_records.count()
        present_lessons = attendance_records.filter(attendance_status='present').count()
        
        attendance_percentage = (present_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        # 3. Рассчитываем общий рейтинг (оценки 70%, посещения 30%)
        if total_lessons > 0 or submissions.count() > 0:  # Только если есть активность
            rating = (grade_percentage * 0.7) + (attendance_percentage * 0.3)
            
            top_students.append({
                'student': student,
                'course': course,
                'grade_percentage': grade_percentage,
                'attendance_percentage': attendance_percentage,
                'rating': rating,
                'total_lessons': total_lessons,
                'present_lessons': present_lessons,
                'submissions_count': submissions.count()
            })
    
    # Сортируем по рейтингу и берем топ-5
    top_students.sort(key=lambda x: x['rating'], reverse=True)
    top_students = top_students[:5]
    
    return {
        'title': 'Лучшие студенты месяца',
        'type': 'top_students',
        'data': top_students,
        'icon': 'fas fa-trophy',
        'color': 'warning'
    }


def get_students_analytics_widget(current_org=None):
    """Виджет общей аналитики студентов"""
    from datetime import datetime
    from apps.assignments.models import AssignmentSubmission
    from apps.courses.models import CourseStudent
    
    # Получаем начало текущего месяца
    current_date = timezone.now()
    month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Фильтруем по организации
    students_filter = {}
    if current_org:
        students_filter['student__organization'] = current_org
    
    # 1. Средний балл всех студентов за месяц
    submissions = AssignmentSubmission.objects.filter(
        submitted_at__gte=month_start,
        status='graded',
        grade__isnull=False
    ).select_related('assignment')
    
    if current_org:
        submissions = submissions.filter(student__organization=current_org)
    
    total_score = 0
    total_max_score = 0
    for submission in submissions:
        if submission.grade is not None and submission.assignment.max_score is not None:
            total_score += submission.grade
            total_max_score += submission.assignment.max_score
    
    average_grade = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    # 2. Средняя посещаемость за месяц
    attendance_records = AttendanceRecord.objects.filter(
        lesson__lesson_date__gte=month_start
    )
    
    if current_org:
        attendance_records = attendance_records.filter(lesson__organization=current_org)
    
    total_lessons = attendance_records.count()
    present_lessons = attendance_records.filter(attendance_status='present').count()
    
    average_attendance = (present_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    # 3. Количество студентов, ушедших с курсов за месяц
    left_students = CourseStudent.objects.filter(
        status='left',
        updated_at__gte=month_start
    )
    
    if current_org:
        left_students = left_students.filter(student__organization=current_org)
    
    left_count = left_students.count()
    
    return {
        'title': 'Аналитика студентов',
        'type': 'students_analytics',
        'data': {
            'average_grade': average_grade,
            'average_attendance': average_attendance,
            'left_count': left_count
        },
        'icon': 'fas fa-chart-line',
        'color': 'info'
    }


def get_ai_prediction_widget(current_org=None):
    """AI-прогноз студентов с использованием Gemini API"""
    from datetime import datetime
    from apps.assignments.models import AssignmentSubmission
    from apps.courses.models import CourseStudent
    from .ai_analytics import analyze_student_with_ai
    
    # Получаем начало текущего месяца
    current_date = timezone.now()
    month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Фильтруем по организации
    students_filter = {}
    if current_org:
        students_filter['student__organization'] = current_org
    
    risk_students = []
    improving_students = []
    
    # Получаем всех активных студентов
    course_students = CourseStudent.objects.filter(
        status='active',
        **students_filter
    ).select_related('student', 'course')
    
    for course_student in course_students:
        student = course_student.student
        course = course_student.course
        
        # Анализ успеваемости за последние 2 недели
        two_weeks_ago = current_date - timedelta(days=14)
        
        # 1. Оценки за последние 2 недели
        recent_submissions = AssignmentSubmission.objects.filter(
            assignment__course=course,
            student=student,
            submitted_at__gte=two_weeks_ago,
            status='graded',
            grade__isnull=False
        ).select_related('assignment')
        
        # 2. Оценки за предыдущий период (2 недели до этого)
        previous_period_start = two_weeks_ago - timedelta(days=14)
        previous_submissions = AssignmentSubmission.objects.filter(
            assignment__course=course,
            student=student,
            submitted_at__gte=previous_period_start,
            submitted_at__lt=two_weeks_ago,
            status='graded',
            grade__isnull=False
        ).select_related('assignment')
        
        # 3. Посещаемость за последние 2 недели
        recent_attendance = AttendanceRecord.objects.filter(
            lesson__course=course,
            student=student,
            lesson__lesson_date__gte=two_weeks_ago
        )
        
        total_recent_lessons = recent_attendance.count()
        present_recent_lessons = recent_attendance.filter(attendance_status='present').count()
        recent_attendance_rate = (present_recent_lessons / total_recent_lessons * 100) if total_recent_lessons > 0 else 0
        
        # Рассчитываем средние баллы
        def calculate_avg_grade(submissions):
            total_score = 0
            total_max_score = 0
            for sub in submissions:
                if sub.grade is not None and sub.assignment.max_score is not None:
                    total_score += sub.grade
                    total_max_score += sub.assignment.max_score
            return (total_score / total_max_score * 100) if total_max_score > 0 else 0
        
        recent_avg = calculate_avg_grade(recent_submissions)
        previous_avg = calculate_avg_grade(previous_submissions)
        
        # AI-прогноз на основе трендов
        if recent_submissions.count() >= 2:  # Только если достаточно данных
            grade_trend = recent_avg - previous_avg
            
            # Данные для AI-анализа
            student_data = {
                'student_name': student.full_name,
                'course_title': course.title,
                'recent_avg': recent_avg,
                'grade_trend': grade_trend,
                'attendance_rate': recent_attendance_rate,
                'absent_count': recent_attendance.filter(attendance_status='absent').count(),
                'failed_count': recent_submissions.filter(grade__lt=60).count(),
                'student': student,
                'course': course
            }
            
            # Анализ с Gemini API
            ai_analyzed_data = analyze_student_with_ai(student_data)
            
            # Классификация на основе AI-анализа
            ai_analysis = ai_analyzed_data.get('ai_analysis', {})
            
            if ai_analysis.get('risk_level') == 'высокий' or ai_analysis.get('prediction') == 'уйдет с курса':
                risk_students.append(ai_analyzed_data)
            elif ai_analysis.get('risk_level') == 'низкий' and ai_analysis.get('prediction') in ['останется', 'улучшится']:
                improving_students.append(ai_analyzed_data)
    
    # Сортируем по AI confidence
    risk_students.sort(key=lambda x: x['ai_analysis'].get('confidence', 0), reverse=True)
    improving_students.sort(key=lambda x: x['ai_analysis'].get('confidence', 0), reverse=True)
    
    return {
        'title': 'AI-прогноз студентов',
        'type': 'ai_prediction',
        'data': {
            'risk_students': risk_students[:12],  # Топ-12 в группе риска
            'improving_students': improving_students[:20]  # Топ-20 улучшающихся
        },
        'icon': 'fas fa-brain',
        'color': 'danger'
    }


def get_analytics_widgets(current_org=None):
    """Получить все виджеты аналитики"""
    return [
        get_attendance_widget(current_org),
        get_courses_distribution_widget(current_org),
        get_students_by_months_widget(current_org),
        get_top_students_widget(current_org),
        get_students_analytics_widget(current_org),
        get_ai_prediction_widget(current_org)
    ]
