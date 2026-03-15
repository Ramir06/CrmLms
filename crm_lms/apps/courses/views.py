from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone

from apps.core.mixins import admin_required
from apps.students.models import Student
from .models import Course, CourseStudent
from .forms import CourseForm, CourseStudentForm, AddTicketsForm, MarkAttendanceForm, AdjustTicketsForm
from .services import TicketService
from .tickets import TicketBalance, TicketTransaction, TicketAttendance


@login_required
@admin_required
def course_list(request):
    from django.db.models import Count, Q as Qm
    qs = Course.objects.filter(is_archived=False).select_related('mentor').annotate(
        active_count=Count('course_students', filter=Qm(course_students__status='active')),
        left_count=Count('course_students', filter=Qm(course_students__status='left')),
        frozen_count=Count('course_students', filter=Qm(course_students__status='frozen')),
    )
    status_filter = request.GET.get('status', '')
    subject_filter = request.GET.get('subject', '')
    search = request.GET.get('q', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if subject_filter:
        qs = qs.filter(subject__icontains=subject_filter)
    if search:
        qs = qs.filter(title__icontains=search)

    subjects = Course.objects.filter(is_archived=False).values_list('subject', flat=True).distinct()
    context = {
        'courses': qs,
        'subjects': subjects,
        'status_filter': status_filter,
        'subject_filter': subject_filter,
        'search': search,
        'page_title': 'Курсы',
    }
    return render(request, 'admin/courses/list.html', context)


@login_required
@admin_required
def course_archive(request):
    courses = Course.objects.filter(is_archived=True).select_related('mentor')
    return render(request, 'admin/courses/archive.html', {'courses': courses, 'page_title': 'Архив курсов'})


def _add_months(d, months):
    import calendar as _cal
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, _cal.monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)


def _generate_lessons_for_course(course):
    """Generate Lesson objects for a course based on its schedule."""
    from apps.lessons.models import Lesson
    from datetime import timedelta, time

    if not course.start_date:
        return 0

    DAY_MAP = {
        'mon_wed_fri': [0, 2, 4],
        'tue_thu_sat': [1, 3, 5],
        'mon_to_fri':  [0, 1, 2, 3, 4],
        'sat_sun':     [5, 6],
        'custom':      [],
    }
    weekdays = DAY_MAP.get(course.days_of_week, [])
    if not weekdays:
        return 0

    end_date = course.end_date or _add_months(course.start_date, course.duration_months)
    start_time = course.lesson_start_time or time(9, 0)
    end_time = course.lesson_end_time or time(10, 30)

    lessons_to_create = []
    current = course.start_date
    while current <= end_date:
        if current.weekday() in weekdays:
            lessons_to_create.append(Lesson(
                course=course,
                lesson_date=current,
                start_time=start_time,
                end_time=end_time,
                room=course.room,
                type='regular',
                status='scheduled',
            ))
        current += timedelta(days=1)

    Lesson.objects.bulk_create(lessons_to_create)
    return len(lessons_to_create)


@login_required
@admin_required
def course_create(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        count = _generate_lessons_for_course(course)
        if count:
            messages.success(request, f'Курс «{course.title}» создан. Автоматически сгенерировано {count} занятий.')
        else:
            messages.success(request, f'Курс «{course.title}» создан.')
        return redirect('courses:detail', pk=course.pk)
    return render(request, 'admin/courses/form.html', {'form': form, 'page_title': 'Создать курс'})


@login_required
@admin_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course_students = CourseStudent.objects.filter(
        course=course
    ).select_related('student').prefetch_related(
        'ticket_balance',
        'ticket_transactions',
        'ticket_attendances'
    ).order_by('student__full_name')
    
    # Separate active and left students
    active_students = course_students.filter(status='active')
    left_students = course_students.filter(status='left')
    
    # Prepare ticket data for unlimited courses
    ticket_data = {}
    if course.is_unlimited:
        for cs in active_students:
            ticket_data[cs.pk] = TicketService.get_student_ticket_summary(cs)

    context = {
        'course': course,
        'course_students': course_students,
        'active_students': active_students,
        'left_students': left_students,
        'ticket_data': ticket_data,
        'page_title': course.title,
    }
    return render(request, 'admin/courses/detail.html', context)


@login_required
@admin_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Курс обновлён.')
        return redirect('courses:detail', pk=pk)
    return render(request, 'admin/courses/form.html', {'form': form, 'course': course, 'page_title': 'Редактировать курс'})


@login_required
@admin_required
def course_add_student(request, pk):
    course = get_object_or_404(Course, pk=pk)
    form = CourseStudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cs = form.save(commit=False)
        cs.course = course
        cs.save()
        messages.success(request, 'Студент добавлен в курс.')
        return redirect('courses:detail', pk=pk)
    return render(request, 'admin/courses/add_student.html', {'form': form, 'course': course, 'page_title': 'Добавить студента'})


@login_required
@admin_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f'Курс «{title}» удалён.')
        return redirect('courses:list')
    return render(request, 'admin/courses/confirm_delete.html', {'course': course})


@login_required
@admin_required
def remove_student(request, pk):
    """Remove a CourseStudent enrollment."""
    from django.utils import timezone
    cs = get_object_or_404(CourseStudent, pk=pk)
    course_pk = cs.course_id
    if request.method == 'POST':
        name = cs.student.full_name
        cs.status = 'left'
        cs.left_at = timezone.now().date()
        cs.save()
        messages.success(request, f'Студент «{name}» покинул курс.')
    return redirect('courses:detail', pk=course_pk)


@login_required
def student_drawer(request, pk):
    """Partial template for student drawer in course detail."""
    cs = get_object_or_404(CourseStudent, pk=pk)
    if request.user.role not in ('admin', 'superadmin') and request.user != cs.course.mentor:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    from apps.attendance.models import AttendanceRecord
    attendance_records = AttendanceRecord.objects.filter(
        student=cs.student, lesson__course=cs.course
    ).select_related('lesson').order_by('-lesson__lesson_date')[:10]

    context = {
        'cs': cs,
        'attendance_records': attendance_records,
    }
    return render(request, 'partials/student_drawer.html', context)


# ===== TICKET VIEWS =====

@login_required
@admin_required
def add_tickets(request, cs_pk):
    """Добавить талоны студенту"""
    cs = get_object_or_404(CourseStudent, pk=cs_pk)
    
    if not cs.course.is_unlimited:
        messages.error(request, 'Талоны можно добавлять только для бесконечных курсов')
        return redirect('courses:detail', pk=cs.course.pk)
    
    if request.method == 'POST':
        form = AddTicketsForm(request.POST)
        if form.is_valid():
            try:
                transaction_obj = TicketService.add_tickets(
                    enrollment=cs,
                    quantity=form.cleaned_data['quantity'],
                    price_per_ticket=form.cleaned_data['price_per_ticket'],
                    created_by=request.user,
                    comment=form.cleaned_data['comment']
                )
                messages.success(
                    request, 
                    f'Добавлено {form.cleaned_data["quantity"]} талонов для {cs.student.full_name}'
                )
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
            return redirect('courses:detail', pk=cs.course.pk)
    else:
        form = AddTicketsForm()
    
    context = {
        'form': form,
        'cs': cs,
        'page_title': f'Добавить талоны - {cs.student.full_name}'
    }
    return render(request, 'admin/courses/add_tickets.html', context)


@login_required
@admin_required
def mark_attendance(request, cs_pk):
    """Отметить посещение"""
    cs = get_object_or_404(CourseStudent, pk=cs_pk)
    
    if not cs.course.is_unlimited:
        messages.error(request, 'Посещение по талонам доступно только для бесконечных курсов')
        return redirect('courses:detail', pk=cs.course.pk)
    
    if request.method == 'POST':
        form = MarkAttendanceForm(request.POST)
        if form.is_valid():
            try:
                transaction_obj, attendance = TicketService.consume_tickets(
                    enrollment=cs,
                    lessons_count=form.cleaned_data['lessons_count'],
                    marked_by=request.user,
                    lesson_date=form.cleaned_data['lesson_date'],
                    comment=form.cleaned_data['comment']
                )
                remaining = TicketService.get_remaining_tickets(cs)
                if remaining < 0:
                    messages.warning(
                        request,
                        f'Отмечено {form.cleaned_data["lessons_count"]} занятий. '
                        f'Перерасход: {abs(remaining)} талон(ов)'
                    )
                else:
                    messages.success(
                        request,
                        f'Отмечено {form.cleaned_data["lessons_count"]} занятий. '
                        f'Осталось: {remaining} талон(ов)'
                    )
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
            return redirect('courses:detail', pk=cs.course.pk)
    else:
        form = MarkAttendanceForm()
    
    context = {
        'form': form,
        'cs': cs,
        'remaining_tickets': TicketService.get_remaining_tickets(cs),
        'page_title': f'Отметить посещение - {cs.student.full_name}'
    }
    return render(request, 'admin/courses/mark_attendance.html', context)


@login_required
@admin_required
def ticket_history(request, cs_pk):
    """История операций с талонами"""
    cs = get_object_or_404(CourseStudent, pk=cs_pk)
    
    if not cs.course.is_unlimited:
        messages.error(request, 'История талонов доступна только для бесконечных курсов')
        return redirect('courses:detail', pk=cs.course.pk)
    
    transactions = cs.ticket_transactions.all().order_by('-created_at')
    attendances = cs.ticket_attendances.all().order_by('-lesson_date')
    
    # Получаем сводку
    summary = TicketService.get_student_ticket_summary(cs)
    
    context = {
        'cs': cs,
        'transactions': transactions,
        'attendances': attendances,
        'summary': summary,
        'page_title': f'История талонов - {cs.student.full_name}'
    }
    return render(request, 'admin/courses/ticket_history.html', context)


@login_required
@admin_required
def adjust_tickets(request, cs_pk):
    """Корректировать количество талонов"""
    cs = get_object_or_404(CourseStudent, pk=cs_pk)
    
    if not cs.course.is_unlimited:
        messages.error(request, 'Корректировка доступна только для бесконечных курсов')
        return redirect('courses:detail', pk=cs.course.pk)
    
    balance = TicketService.get_or_create_balance(cs)
    
    if request.method == 'POST':
        form = AdjustTicketsForm(request.POST)
        if form.is_valid():
            try:
                transaction_obj = TicketService.adjust_tickets(
                    enrollment=cs,
                    new_total=form.cleaned_data['new_total'],
                    created_by=request.user,
                    comment=form.cleaned_data['comment']
                )
                messages.success(
                    request,
                    f'Количество талонов скорректировано до {form.cleaned_data["new_total"]}'
                )
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
            return redirect('courses:detail', pk=cs.course.pk)
    else:
        form = AdjustTicketsForm(initial={'new_total': balance.total_tickets})
    
    context = {
        'form': form,
        'cs': cs,
        'balance': balance,
        'page_title': f'Корректировать талоны - {cs.student.full_name}'
    }
    return render(request, 'admin/courses/adjust_tickets.html', context)
