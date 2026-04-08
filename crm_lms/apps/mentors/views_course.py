from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q
from apps.courses.models import Course, CourseStudent
from apps.students.models import Student
from apps.courses.forms import CourseStudentForm


@login_required
def mentor_course_detail(request, course_id):
    """Страница курса для ментора с информацией о студентах"""
    course = get_object_or_404(Course, id=course_id)
    
    # Проверяем, является ли пользователь ментором этого курса
    if course.mentor != request.user:
        return HttpResponseForbidden("Вы не являетесь ментором этого курса")
    
    # Получаем студентов курса
    course_students = CourseStudent.objects.filter(
        course=course
    ).select_related('student').prefetch_related(
        'ticket_balance',
    ).order_by('student__full_name')
    
    # Разделяем активных и ушедших студентов
    active_students = course_students.filter(status='active')
    left_students = course_students.filter(status='left')
    
    context = {
        'current_course': course,
        'course': course,
        'page_title': f'Курс: {course.title}',
        'course_students': course_students,
        'active_students': active_students,
        'left_students': left_students,
    }
    return render(request, 'mentors/course_detail.html', context)


@login_required
def mentor_course_students(request, course_id):
    """Страница со списком студентов курса с возможностью добавления"""
    course = get_object_or_404(Course, id=course_id)
    
    # Проверяем, является ли пользователь ментором этого курса
    if course.mentor != request.user:
        return HttpResponseForbidden("Вы не являетесь ментором этого курса")
    
    # Получаем студентов курса
    course_students = CourseStudent.objects.filter(
        course=course
    ).select_related('student').prefetch_related(
        'ticket_balance',
    ).order_by('student__full_name')
    
    # Разделяем активных и ушедших студентов
    active_students = course_students.filter(status='active')
    left_students = course_students.filter(status='left')
    
    # Форма добавления студента
    form = CourseStudentForm(request.POST or None)
    
    # Фильтруем доступных студентов (только из организации курса)
    if course.organization:
        available_students = Student.objects.filter(
            organization=course.organization,
            status='active'
        ).exclude(
            id__in=course_students.values_list('student_id', flat=True)
        )
    else:
        available_students = Student.objects.filter(
            status='active'
        ).exclude(
            id__in=course_students.values_list('student_id', flat=True)
        )
    
    # Поиск по студентам
    search = request.GET.get('search', '')
    if search:
        available_students = available_students.filter(
            Q(full_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__phone__icontains=search)
        )
    
    if request.method == 'POST' and form.is_valid():
        cs = form.save(commit=False)
        cs.course = course
        cs.save()
        messages.success(request, 'Студент добавлен в курс.')
        return redirect('mentors:course_students', course_id=course_id)
    
    context = {
        'current_course': course,
        'course': course,
        'page_title': f'Студенты курса: {course.title}',
        'course_students': course_students,
        'active_students': active_students,
        'left_students': left_students,
        'form': form,
        'available_students': available_students,
        'search': search,
    }
    return render(request, 'mentors/course_students.html', context)
