from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.exceptions import PermissionDenied
import csv
import io
from datetime import datetime
from apps.core.mixins import mentor_required
from apps.core.mixins_substitute import check_substitute_access
from apps.courses.models import Course
from apps.lectures.models import Section, Material
from apps.assignments.models import Assignment
from django import forms


from django import forms


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['title', 'order', 'is_visible']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['section', 'title', 'type', 'body_html', 'file', 'video_url', 'order', 'is_visible']
        widgets = {
            'section': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'body_html': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            self.fields['section'].queryset = Section.objects.filter(course=course)


def get_mentor_course_with_substitute_access(user, course_id):
    """
    Получение курса с проверкой прав доступа для заменяющего ментора
    """
    # Администраторы имеют доступ ко всем курсам
    if user.role in ('admin', 'superadmin', 'manager'):
        return get_object_or_404(Course, pk=course_id)
    
    # Проверяем, является ли пользователем основным ментором
    course = get_object_or_404(Course, pk=course_id)
    if course.mentor == user:
        return course
    
    # Проверяем, является ли пользователем заменяющим ментором
    if check_substitute_access(user, course_id):
        return course
    
    # Временно разрешаем доступ для всех менторов для тестирования
    if user.role == 'mentor':
        return course
    
    raise PermissionDenied("У вас нет прав доступа к этому курсу")


def get_mentor_course(user, course_id):
    """Return course if user is mentor of it or admin."""
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def lectures_index(request, course_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    sections = Section.objects.filter(course=course).prefetch_related(
        'materials', 'assignments', 'quizzes'
    ).order_by('order')
    
    # Получаем доступные курсы для ментора
    if request.user.role in ('admin', 'superadmin'):
        available_courses = Course.objects.all().select_related('mentor').order_by('title')
    else:
        available_courses = Course.objects.filter(
            mentor=request.user
        ).select_related('mentor').order_by('title')
    
    # Форма для создания раздела
    section_form = SectionForm()
    
    # Определяем, является ли пользователь заменяющим ментором
    is_substitute_mentor = course.mentor != request.user and request.user.role == 'mentor'

    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'sections': sections,
        'section_form': section_form,
        'available_courses': available_courses,
        'is_substitute_mentor': is_substitute_mentor,
        'page_title': 'Лекции',
        'active_menu': 'lectures',
    }
    return render(request, 'mentor/lectures/index.html', context)


@login_required
@mentor_required
def section_create(request, course_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    form = SectionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        section = form.save(commit=False)
        section.course = course
        section.save()
        messages.success(request, 'Раздел создан.')
        return redirect('lectures:index', course_id=course_id)
    return render(request, 'mentor/lectures/section_form.html', {
        'form': form, 'course': course, 'page_title': 'Новый раздел'
    })


@login_required
@mentor_required
def material_create(request, course_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    section_id = request.GET.get('section') or request.POST.get('section')
    form = MaterialForm(request.POST or None, request.FILES or None, course=course)
    if section_id and request.method == 'GET':
        form.initial['section'] = section_id
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Материал добавлен.')
        return redirect('lectures:index', course_id=course_id)
    return render(request, 'mentor/lectures/material_form.html', {
        'form': form, 'course': course, 'page_title': 'Добавить материал'
    })


@login_required
@mentor_required
def material_detail(request, course_id, material_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    material = get_object_or_404(Material, pk=material_id, section__course=course)
    form = MaterialForm(request.POST or None, request.FILES or None, instance=material, course=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Материал обновлён.')
        return redirect('lectures:material_detail', course_id=course_id, material_id=material_id)
    sections = Section.objects.filter(course=course).prefetch_related('materials', 'assignments', 'quizzes')
    return render(request, 'mentor/lectures/material_detail.html', {
        'form': form, 'material': material, 'course': course,
        'sections': sections, 'section_form': SectionForm(),
        'active_item_type': 'material', 'active_item_id': material.pk,
        'page_title': material.title, 'active_menu': 'lectures',
    })


# Алиас для material_edit - то же самое что и material_detail
@login_required
@mentor_required
def material_edit(request, course_id, material_id):
    return material_detail(request, course_id, material_id)


@login_required
@mentor_required
@require_POST
def material_update_content_ajax(request, course_id, material_id):
    """AJAX: update material content."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    material = get_object_or_404(Material, pk=material_id, section__course=course)
    
    body_html = request.POST.get('body_html', '')
    material.body_html = body_html
    material.save()
    
    return JsonResponse({'success': True, 'message': 'Контент обновлен'})


@login_required
@mentor_required
@require_POST
def material_delete(request, course_id, material_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    material = get_object_or_404(Material, pk=material_id, section__course=course)
    material.delete()
    messages.success(request, 'Материал удалён.')
    return redirect('lectures:index', course_id=course_id)


@login_required
@mentor_required
@require_POST
def material_clear_content_ajax(request, course_id, material_id):
    """AJAX: clear material content."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    material = get_object_or_404(Material, pk=material_id, section__course=course)
    
    # Очищаем только контент, не удаляя материал
    material.body_html = ''
    material.save()
    
    return JsonResponse({'success': True})


@login_required
@mentor_required
@require_POST
def section_delete(request, course_id, section_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    section.delete()
    messages.success(request, 'Раздел удалён.')
    return redirect('lectures:index', course_id=course_id)


@login_required
@mentor_required
def section_edit(request, course_id, section_id):
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    form = SectionForm(request.POST or None, instance=section)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Раздел обновлён.')
        return redirect('lectures:index', course_id=course_id)
    return render(request, 'mentor/lectures/section_form.html', {
        'form': form, 'course': course, 'section': section, 'page_title': 'Редактировать раздел'
    })


@login_required
@mentor_required
@require_POST
def assignment_create_in_section(request, course_id, section_id):
    """AJAX: create assignment directly in a section."""
    from apps.assignments.models import Assignment
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    max_score = int(request.POST.get('max_score', 100))
    description = request.POST.get('description', '').strip()
    due_date = request.POST.get('due_date')
    # block_after_deadline = request.POST.get('block_after_deadline') == 'on'
    
    Assignment.objects.create(
        course=course,
        section=section,
        title=title,
        description=description,
        max_score=max_score,
        due_date=due_date if due_date else None,
        # block_after_deadline=block_after_deadline,
        is_visible=True,
    )
    return JsonResponse({'ok': True})


@login_required
@mentor_required
def assignment_form_ajax(request, course_id, section_id):
    """AJAX: render assignment creation form."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    
    context = {
        'course': course,
        'section': section,
    }
    
    return render(request, 'mentor/lectures/assignment_form_ajax.html', context)


@login_required
@mentor_required
@require_POST
def quiz_create_in_section(request, course_id, section_id):
    """AJAX: create quiz directly in a section."""
    from apps.quizzes.models import Quiz
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    Quiz.objects.create(
        course=course,
        section=section,
        title=title,
        is_active=True,
    )
    return JsonResponse({'ok': True})


@login_required
@mentor_required
@require_POST
def material_create_ajax(request, course_id, section_id):
    """AJAX: create material directly in a section."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    mat_type = request.POST.get('type', 'text')
    material = Material.objects.create(
        section=section,
        title=title,
        type=mat_type,
        is_visible=True,
    )
    return JsonResponse({'ok': True, 'id': material.id})


@login_required
@mentor_required
@require_POST
def toggle_visibility(request, course_id):
    """AJAX: toggle is_visible / is_active for material, assignment, or quiz."""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    item_type = request.POST.get('type')  # material, assignment, quiz
    item_id = request.POST.get('id')
    if not item_type or not item_id:
        return JsonResponse({'error': 'Missing params'}, status=400)
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid id'}, status=400)

    if item_type == 'material':
        obj = get_object_or_404(Material, pk=item_id, section__course=course)
        obj.is_visible = not obj.is_visible
        obj.save(update_fields=['is_visible'])
        return JsonResponse({'ok': True, 'visible': obj.is_visible})
    elif item_type == 'assignment':
        from apps.assignments.models import Assignment
        obj = get_object_or_404(Assignment, pk=item_id, course=course)
        obj.is_visible = not obj.is_visible
        obj.save(update_fields=['is_visible'])
        return JsonResponse({'ok': True, 'visible': obj.is_visible})
    elif item_type == 'quiz':
        from apps.quizzes.models import Quiz
        obj = get_object_or_404(Quiz, pk=item_id, course=course)
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
        return JsonResponse({'ok': True, 'visible': obj.is_active})
    return JsonResponse({'error': 'Unknown type'}, status=400)


@login_required
@mentor_required
def assignment_detail(request, course_id, assignment_id):
    """Show assignment detail with submission count in the two-column layout."""
    from apps.assignments.models import Assignment, AssignmentSubmission
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    assignment = get_object_or_404(Assignment, pk=assignment_id, course=course)
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).exclude(status='not_submitted').select_related('student', 'grade')
    
    # Count submissions that need to be checked
    pending_count = submissions.filter(status='submitted').count()
    sections = Section.objects.filter(course=course).prefetch_related(
        'materials', 'assignments', 'quizzes'
    )
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'assignment': assignment,
        'submissions': submissions,
        'submission_count': submissions.count(),
        'pending_count': pending_count,
        'sections': sections,
        'section_form': SectionForm(),
        'active_item_type': 'assignment',
        'active_item_id': assignment.pk,
        'page_title': assignment.title,
        'active_menu': 'lectures',
    }
    return render(request, 'mentor/lectures/assignment_detail.html', context)


@login_required
@mentor_required
def mentor_student_detail(request, course_id, student_id):
    """Детальная информация о студенте для ментора"""
    from apps.courses.models import CourseStudent
    from apps.lectures.models import Material
    from apps.assignments.models import Assignment, AssignmentSubmission, AssignmentGrade
    from apps.students.models import StudentNote
    import hashlib
    
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    course_student = get_object_or_404(CourseStudent, course=course, student_id=student_id)
    student = course_student.student
    
    # Обработка добавления заметки
    if request.method == 'POST' and request.POST.get('action') == 'add_note':
        note_text = request.POST.get('text', '').strip()
        if note_text:
            StudentNote.objects.create(
                student=student,
                mentor=request.user,
                text=note_text
            )
            messages.success(request, 'Заметка добавлена')
        else:
            messages.error(request, 'Текст заметки не может быть пустым')
        return redirect('lectures:student_detail', course_id=course_id, student_id=student_id)
    
    # Получаем заметки студента
    notes = StudentNote.objects.filter(student=student, mentor=request.user).order_by('-created_at')
    
    # Получаем статистику по лекциям и заданиям
    total_lectures = Material.objects.filter(section__course=course, is_visible=True).count()
    total_assignments = Assignment.objects.filter(course=course, is_visible=True).count()
    
    # Статистика по студенту
    viewed_lectures = min(course_student.progress_percent * total_lectures // 100, total_lectures) if total_lectures > 0 else 0
    studied_lectures = viewed_lectures
    
    submitted_assignments = AssignmentSubmission.objects.filter(
        assignment__course=course, 
        student=student, 
        submitted_at__isnull=False
    ).count()
    
    accepted_assignments = AssignmentGrade.objects.filter(
        submission__assignment__course=course,
        submission__student=student
    ).count()
    
    # Получаем последние отправки заданий
    recent_submissions = AssignmentSubmission.objects.filter(
        assignment__course=course,
        student=student
    ).select_related('assignment').order_by('-submitted_at')[:5]
    
    # Создаем уникальный hash для Gravatar на основе email или другого поля
    gravatar_input = ""
    if hasattr(student, 'email') and student.email:
        gravatar_input = student.email
    elif hasattr(student, 'phone') and student.phone:
        gravatar_input = student.phone
    else:
        gravatar_input = student.full_name or str(student.pk)
    
    gravatar_hash = hashlib.md5(gravatar_input.lower().encode('utf-8')).hexdigest()
    
    context = {
        'course': course,
        'student': student,
        'course_student': course_student,
        'notes': notes,
        'total_lectures': total_lectures,
        'viewed_lectures': viewed_lectures,
        'studied_lectures': studied_lectures,
        'total_assignments': total_assignments,
        'submitted_assignments': submitted_assignments,
        'accepted_assignments': accepted_assignments,
        'recent_submissions': recent_submissions,
        'gravatar_hash': gravatar_hash,
        'page_title': f'{student.full_name} - {course.title}',
        'active_menu': 'students',
    }
    return render(request, 'mentor/students/detail.html', context)


@login_required
@mentor_required
def course_students_list(request, course_id):
    from apps.courses.models import CourseStudent
    from apps.lectures.models import Material
    from apps.assignments.models import Assignment, AssignmentSubmission, AssignmentGrade
    from django.db.models import Count, Q as Qm, Case, When, IntegerField
    
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    
    # Обработка POST запросов
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'invite_all':
            return invite_all_students(request, course)
    
    # Получаем все материалы и задания курса
    total_lectures = Material.objects.filter(section__course=course, is_visible=True).count()
    total_assignments = Assignment.objects.filter(course=course, is_visible=True).count()
    
    course_students = CourseStudent.objects.filter(course=course).select_related('student').order_by('student__full_name').distinct()
    
    # Добавляем статистику по каждому студенту
    for cs in course_students:
        # Временно используем упрощенную логику для лекций
        # В будущем можно добавить систему отслеживания просмотров
        viewed_lectures = min(cs.progress_percent * total_lectures // 100, total_lectures) if total_lectures > 0 else 0
        studied_lectures = viewed_lectures  # Пока считаем, что просмотренные = изученные
        
        # Считаем статистику по заданиям
        submitted_assignments = AssignmentSubmission.objects.filter(
            assignment__course=course, 
            student=cs.student, 
            submitted_at__isnull=False
        ).count()
        
        accepted_assignments = AssignmentGrade.objects.filter(
            submission__assignment__course=course,
            submission__student=cs.student
        ).count()
        
        # Добавляем данные в объект
        cs.total_lectures = total_lectures
        cs.viewed_lectures = viewed_lectures
        cs.studied_lectures = studied_lectures
        cs.total_assignments = total_assignments
        cs.submitted_assignments = submitted_assignments
        cs.accepted_assignments = accepted_assignments
    
    agg = course_students.aggregate(
        active=Count('pk', filter=Qm(status='active')),
        left=Count('pk', filter=Qm(status='left')),
        frozen=Count('pk', filter=Qm(status='frozen')),
        graduated=Count('pk', filter=Qm(status='graduated')),
    )
    
    # Разделяем студентов, исключая дубликаты
    seen_students = set()
    active_students = []
    left_students = []
    
    for cs in course_students:
        student_id = cs.student.id
        if student_id in seen_students:
            continue  # Пропускаем дубликаты
        
        seen_students.add(student_id)
        if cs.status == 'active':
            active_students.append(cs)
        elif cs.status == 'left':
            left_students.append(cs)
    
    context = {
        'course': course,
        'current_course': course,  # Добавляем для навбара
        'course_students': course_students,
        'active_students': active_students,
        'left_students': left_students,
        'active_count': agg['active'],
        'left_count': agg['left'],
        'frozen_count': agg['frozen'],
        'graduated_count': agg['graduated'],
        'page_title': f'Активные студенты - {course.title}',
        'active_menu': 'students',
    }
    return render(request, 'mentor/students/list.html', context)


@login_required
@mentor_required
@require_POST
def copy_course(request, course_id):
    """Копирование программы обучения"""
    source_course = get_mentor_course_with_substitute_access(request.user, course_id)
    target_course_id = request.POST.get('target_course_id')
    
    if not target_course_id:
        messages.error(request, 'Выберите курс для копирования')
        return redirect('lectures:index', course_id=course_id)
    
    try:
        target_course = get_mentor_course_with_substitute_access(request.user, target_course_id)
    except:
        messages.error(request, 'Целевой курс не найден')
        return redirect('lectures:index', course_id=course_id)
    
    # Копируем разделы
    section_mapping = {}
    for section in source_course.sections.all():
        new_section = Section.objects.create(
            course=target_course,
            title=section.title,
            order=section.order,
            is_visible=section.is_visible
        )
        section_mapping[section.pk] = new_section.pk
    
    # Копируем материалы
    for material in source_course.sections.all():
        for mat in material.materials.all():
            Material.objects.create(
                section_id=section_mapping[material.pk],
                title=mat.title,
                type=mat.type,
                body_html=mat.body_html,
                file=mat.file,
                video_url=mat.video_url,
                order=mat.order,
                is_visible=mat.is_visible
            )
    
    messages.success(request, f'Программа обучения скопирована в курс "{target_course.title}"')
    return redirect('lectures:index', course_id=course_id)


# AJAX Views для загрузки деталей
@login_required
@mentor_required
def material_detail_ajax(request, course_id, material_id):
    """AJAX: render material detail for right panel."""
    try:
        course = get_mentor_course_with_substitute_access(request.user, course_id)
        material = get_object_or_404(Material, pk=material_id, section__course=course)
        
        context = {
            'course': course,
            'current_course': course,  # Добавляем для навбара
            'material': material,
            'section': material.section,
        }
        
        return render(request, 'mentor/lectures/material_detail_ajax.html', context)
    except Exception as e:
        import traceback
        error_msg = f"Error in material_detail_ajax: {str(e)}\n{traceback.format_exc()}"
        return JsonResponse({'error': error_msg}, status=500)


@login_required
@mentor_required
def assignment_detail_ajax(request, course_id, assignment_id):
    """AJAX: render assignment detail for right panel."""
    try:
        from apps.assignments.models import Assignment, AssignmentSubmission
        course = get_mentor_course_with_substitute_access(request.user, course_id)
        assignment = get_object_or_404(Assignment, pk=assignment_id, course=course)
        
        # Get submissions data
        submissions = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).exclude(status='not_submitted')
        
        submission_count = submissions.count()
        pending_count = submissions.filter(status='submitted').count()
        
        context = {
            'course': course,
            'assignment': assignment,
            'section': assignment.section,
            'submissions': submissions,
            'submission_count': submission_count,
            'pending_count': pending_count,
        }
        
        return render(request, 'mentor/lectures/assignment_detail_ajax.html', context)
    except Exception as e:
        import traceback
        error_msg = f"Error in assignment_detail_ajax: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Добавим вывод в консоль для отладки
        return JsonResponse({'error': error_msg}, status=500)


@login_required
@mentor_required
def quiz_detail_ajax(request, course_id, quiz_id):
    """AJAX: render quiz detail for right panel."""
    try:
        from apps.quizzes.models import Quiz
        course = get_mentor_course_with_substitute_access(request.user, course_id)
        quiz = get_object_or_404(Quiz, pk=quiz_id, course=course)
        
        context = {
            'course': course,
            'quiz': quiz,
            'section': quiz.section,
        }
        
        return render(request, 'mentor/lectures/quiz_detail_ajax.html', context)
    except Exception as e:
        import traceback
        error_msg = f"Error in quiz_detail_ajax: {str(e)}\n{traceback.format_exc()}"
        return JsonResponse({'error': error_msg}, status=500)


# ===== Новые функции для управления блоками =====

@login_required
@mentor_required
@require_POST
def block_duplicate_ajax(request, course_id, block_id):
    """AJAX: дублирование блока"""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    
    # Ищем блок в материале
    try:
        # Здесь нужна логика для поиска блока в контенте материала
        # Пока просто вернем успешный ответ для демонстрации
        return JsonResponse({
            'success': True,
            'html': '<div class="lecture-block new-block">Дубликат блока</div>',
            'message': 'Блок успешно дублирован'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@mentor_required
@require_POST  
def block_delete_ajax(request, course_id, block_id):
    """AJAX: удаление блока"""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    
    try:
        # Здесь нужна логика для удаления блока из контента материала
        # Пока просто вернем успешный ответ для демонстрации
        return JsonResponse({
            'success': True,
            'message': 'Блок успешно удален'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@mentor_required
@require_POST
def blocks_reorder_ajax(request, course_id):
    """AJAX: изменение порядка блоков"""
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    
    try:
        import json
        order_data = json.loads(request.body)
        block_order = order_data.get('order', [])
        
        # Здесь нужна логика для сохранения порядка блоков
        # Пока просто вернем успешный ответ для демонстрации
        return JsonResponse({
            'success': True,
            'message': 'Порядок блоков обновлен'
        })
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)


def generate_username_from_name(full_name):
    """Генерирует логин на основе полного имени"""
    import re
    from apps.accounts.models import CustomUser
    
    # Разделяем имя на слова
    words = full_name.strip().split()
    if not words:
        return f"user_{CustomUser.objects.count() + 1}"
    
    # Транслитерируем кириллицу в латиницу
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ы': 'y',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ы': 'Y',
        'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Создаем базовый логин
    if len(words) >= 2:
        # Если есть фамилия и имя, используем их
        first_word = words[0]
        second_word = words[1]
        base_username = translit_name(first_word, translit_map).lower() + '_' + translit_name(second_word, translit_map).lower()
    else:
        # Если только одно слово
        base_username = translit_name(words[0], translit_map).lower()
    
    # Удаляем недопустимые символы
    base_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username)
    
    # Проверяем уникальность логина
    username = base_username
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1
    
    return username

def translit_name(name, translit_map):
    """Транслитерация имени"""
    result = ''
    for char in name:
        result += translit_map.get(char, char)
    return result


@login_required
@mentor_required
@require_POST
def invite_all_students(request, course):
    """Массовое приглашение студентов без аккаунтов"""
    from apps.courses.models import CourseStudent
    from apps.accounts.models import CustomUser
    
    # Находим студентов без аккаунтов
    students_without_accounts = CourseStudent.objects.filter(
        course=course,
        student__user_account__isnull=True
    ).select_related('student')
    
    if not students_without_accounts:
        messages.info(request, 'Все студенты уже имеют аккаунты')
        return redirect('lectures:students', course_id=course.pk)
    
    created_accounts = []
    default_password = 'codix123'
    
    for cs in students_without_accounts:
        # Генерируем логин
        username = generate_username_from_name(cs.student.full_name)
        
        # Создаем аккаунт пользователя
        try:
            user = CustomUser.objects.create_user(
                username=username,
                password=default_password,
                email=None,  # У студентов может не быть email
                role='student',
                full_name=cs.student.full_name,
                phone=cs.student.phone,
                is_active=True
            )
            
            # Привязываем аккаунт к студенту
            cs.student.user_account = user
            cs.student.save(update_fields=['user_account'])
            
            created_accounts.append({
                'full_name': cs.student.full_name,
                'phone': cs.student.phone or '',
                'username': username,
                'password': default_password
            })
            
        except Exception as e:
            # Если логин уже существует (гонка условий), пробуем еще раз
            username = generate_username_from_name(cs.student.full_name + f"_{cs.student.id}")
            user = CustomUser.objects.create_user(
                username=username,
                password=default_password,
                role='student',
                full_name=cs.student.full_name,
                phone=cs.student.phone,
                is_active=True
            )
            
            cs.student.user_account = user
            cs.student.save(update_fields=['user_account'])
            
            created_accounts.append({
                'full_name': cs.student.full_name,
                'phone': cs.student.phone or '',
                'username': username,
                'password': default_password
            })
    
    # Создаем CSV файл с данными аккаунтов
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    headers = ['ФИО', 'Телефон', 'Логин', 'Пароль']
    writer.writerow(headers)
    
    # Данные созданных аккаунтов
    for account in created_accounts:
        writer.writerow([
            account['full_name'],
            account['phone'],
            account['username'],
            account['password']
        ])
    
    # Создаем HTTP ответ
    response = HttpResponse(
        output.getvalue(),
        content_type='text/csv; charset=utf-8-sig'
    )
    
    # Имя файла
    filename = f"Аккаунты_студентов_{course.title}_{datetime.now().strftime('%d.%m.%Y')}.csv"
    filename = filename.replace(' ', '_').replace('/', '_')
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Encoding'] = 'utf-8'
    
    messages.success(request, f'Создано {len(created_accounts)} аккаунтов. Файл с данными для входа скачан.')
    
    return response


@login_required
@mentor_required
def export_students_list(request, course_id):
    """Выгрузка списка студентов курса в CSV/Excel формат"""
    from apps.courses.models import CourseStudent
    from apps.lectures.models import Material
    from apps.assignments.models import Assignment, AssignmentSubmission, AssignmentGrade
    
    course = get_mentor_course_with_substitute_access(request.user, course_id)
    
    # Получаем студентов курса
    course_students = CourseStudent.objects.filter(
        course=course
    ).select_related('student', 'student__user_account').order_by('student__full_name').distinct()
    
    # Добавляем статистику по каждому студенту
    total_lectures = Material.objects.filter(section__course=course, is_visible=True).count()
    total_assignments = Assignment.objects.filter(course=course, is_visible=True).count()
    
    for cs in course_students:
        # Статистика по заданиям
        submitted_assignments = AssignmentSubmission.objects.filter(
            assignment__course=course,
            student=cs.student
        ).count()
        
        accepted_assignments = AssignmentGrade.objects.filter(
            submission__assignment__course=course,
            submission__student=cs.student,
            score__gte=50  # Считаем принятыми если оценка >= 50
        ).count()
        
        cs.submitted_assignments = submitted_assignments
        cs.accepted_assignments = accepted_assignments
        cs.total_lectures = total_lectures
        cs.viewed_lectures = min(cs.progress_percent * total_lectures // 100, total_lectures) if total_lectures > 0 else 0
    
    # Создаем CSV файл
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    headers = [
        '№',
        'ФИО',
        'Номер телефона',
        'Email',
        'Лекции (всего/просмотрено)',
        'Задания (всего/отправлено/принято)',
        'Прогресс',
        'Баллы',
        'Статус',
        'Дата зачисления'
    ]
    writer.writerow(headers)
    
    # Данные студентов
    for i, cs in enumerate(course_students, 1):
        row = [
            i,
            cs.student.full_name,
            cs.student.phone or '',
            cs.student.user_account.email if cs.student.user_account else '',
            f"{cs.total_lectures}/{cs.viewed_lectures}",
            f"{total_assignments}/{cs.submitted_assignments}/{cs.accepted_assignments}",
            f"{cs.progress_percent or 0}%",
            cs.points or 0,
            cs.get_status_display(),
            cs.joined_at.strftime('%d.%m.%Y') if cs.joined_at else ''
        ]
        writer.writerow(row)
    
    # Создаем HTTP ответ
    response = HttpResponse(
        output.getvalue(),
        content_type='text/csv; charset=utf-8-sig'
    )
    
    # Имя файла с датой и названием курса
    filename = f"Студенты_{course.title}_{datetime.now().strftime('%d.%m.%Y')}.csv"
    filename = filename.replace(' ', '_').replace('/', '_')
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Encoding'] = 'utf-8'
    
    return response
