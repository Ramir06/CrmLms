from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q

from apps.core.mixins import admin_required
from .models import Student
from .forms import StudentForm


@login_required
@admin_required
def student_list(request):
    from apps.courses.models import Course
    qs = Student.objects.select_related('user_account').prefetch_related('course_enrollments__course').all()
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    subject_filter = request.GET.get('subject', '')

    if search:
        qs = qs.filter(Q(full_name__icontains=search) | Q(phone__icontains=search))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if subject_filter:
        qs = qs.filter(course_enrollments__course__subject__icontains=subject_filter).distinct()

    subjects = Course.objects.exclude(subject='').values_list('subject', flat=True).distinct().order_by('subject')
    
    # Separate students who left courses
    active_students = []
    left_students = []
    
    for student in qs:
        has_left_course = student.course_enrollments.filter(status='left').exists()
        if has_left_course:
            left_students.append(student)
        else:
            active_students.append(student)

    context = {
        'active_students': active_students,
        'left_students': left_students,
        'search': search,
        'status_filter': status_filter,
        'subject_filter': subject_filter,
        'subjects': subjects,
        'page_title': 'Студенты',
    }
    return render(request, 'admin/students/list.html', context)


@login_required
@admin_required
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        student = form.save()
        messages.success(request, f'Студент «{student.full_name}» создан.')
        return redirect('admin_students:detail', pk=student.pk)
    return render(request, 'admin/students/form.html', {'form': form, 'page_title': 'Добавить студента'})


@login_required
@admin_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    enrollments = student.course_enrollments.select_related('course').all()
    payments = student.payments.select_related('course').order_by('-paid_at')[:10]
    debts = student.debts.filter(status='active')
    context = {
        'student': student,
        'enrollments': enrollments,
        'payments': payments,
        'debts': debts,
        'page_title': student.full_name,
    }
    return render(request, 'admin/students/detail.html', context)


@login_required
@admin_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Данные студента обновлены.')
        return redirect('admin_students:detail', pk=pk)
    return render(request, 'admin/students/form.html', {
        'form': form, 'student': student, 'page_title': 'Редактировать студента'
    })


@login_required
@admin_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Студент «{name}» удалён.')
        return redirect('admin_students:list')
    return render(request, 'admin/students/confirm_delete.html', {'student': student})


@login_required
@admin_required
def student_block(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST' and student.user_account:
        user = student.user_account
        user.is_active = not user.is_active
        user.save()
        if user.is_active:
            messages.success(request, f'Аккаунт «{student.full_name}» разблокирован.')
        else:
            messages.warning(request, f'Аккаунт «{student.full_name}» заблокирован.')
    return redirect('admin_students:detail', pk=pk)


@login_required
@admin_required
def student_reset_password(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST' and student.user_account:
        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            student.user_account.set_password(new_password)
            student.user_account.save()
            messages.success(request, f'Пароль для «{student.full_name}» сброшен.')
        else:
            messages.error(request, 'Введите новый пароль.')
    return redirect('admin_students:detail', pk=pk)


@login_required
@admin_required
def student_export(request):
    import openpyxl
    from django.utils import timezone

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Студенты'
    headers = ['ID', 'Имя', 'Телефон', 'Родитель', 'Телефон родителя', 'Источник', 'Статус', 'Дата добавления']
    ws.append(headers)

    for s in Student.objects.all():
        ws.append([
            s.pk, s.full_name, s.phone, s.parent_name, s.parent_phone,
            s.source, s.status, s.created_at.strftime('%Y-%m-%d') if s.created_at else '',
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=students_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response
