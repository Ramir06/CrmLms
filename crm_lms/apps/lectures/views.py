from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.core.mixins import mentor_required
from apps.courses.models import Course
from .models import Section, Material


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
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            self.fields['section'].queryset = Section.objects.filter(course=course)


def get_mentor_course(user, course_id):
    """Return course if user is mentor of it or admin."""
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    return get_object_or_404(Course, pk=course_id, mentor=user)


@login_required
@mentor_required
def lectures_index(request, course_id):
    course = get_mentor_course(request.user, course_id)
    sections = Section.objects.filter(course=course).prefetch_related(
        'materials', 'assignments', 'quizzes'
    )
    section_form = SectionForm()

    context = {
        'course': course,
        'sections': sections,
        'section_form': section_form,
        'page_title': 'Лекции',
        'active_menu': 'lectures',
    }
    return render(request, 'mentor/lectures/index.html', context)


@login_required
@mentor_required
def section_create(request, course_id):
    course = get_mentor_course(request.user, course_id)
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
    course = get_mentor_course(request.user, course_id)
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
    course = get_mentor_course(request.user, course_id)
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


@login_required
@mentor_required
@require_POST
def material_delete(request, course_id, material_id):
    course = get_mentor_course(request.user, course_id)
    material = get_object_or_404(Material, pk=material_id, section__course=course)
    material.delete()
    messages.success(request, 'Материал удалён.')
    return redirect('lectures:index', course_id=course_id)


@login_required
@mentor_required
@require_POST
def section_delete(request, course_id, section_id):
    course = get_mentor_course(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    section.delete()
    messages.success(request, 'Раздел удалён.')
    return redirect('lectures:index', course_id=course_id)


@login_required
@mentor_required
def section_edit(request, course_id, section_id):
    course = get_mentor_course(request.user, course_id)
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
    course = get_mentor_course(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    max_score = int(request.POST.get('max_score', 100))
    Assignment.objects.create(
        course=course,
        section=section,
        title=title,
        max_score=max_score,
        is_visible=True,
    )
    return JsonResponse({'ok': True})


@login_required
@mentor_required
@require_POST
def quiz_create_in_section(request, course_id, section_id):
    """AJAX: create quiz directly in a section."""
    from apps.quizzes.models import Quiz
    course = get_mentor_course(request.user, course_id)
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
    course = get_mentor_course(request.user, course_id)
    section = get_object_or_404(Section, pk=section_id, course=course)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    mat_type = request.POST.get('type', 'text')
    Material.objects.create(
        section=section,
        title=title,
        type=mat_type,
        is_visible=True,
    )
    return JsonResponse({'ok': True})


@login_required
@mentor_required
@require_POST
def toggle_visibility(request, course_id):
    """AJAX: toggle is_visible / is_active for material, assignment, or quiz."""
    course = get_mentor_course(request.user, course_id)
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
    course = get_mentor_course(request.user, course_id)
    assignment = get_object_or_404(Assignment, pk=assignment_id, course=course)
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).exclude(status='not_submitted').select_related('student', 'grade')
    sections = Section.objects.filter(course=course).prefetch_related(
        'materials', 'assignments', 'quizzes'
    )
    context = {
        'course': course,
        'assignment': assignment,
        'submissions': submissions,
        'submission_count': submissions.count(),
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
def course_students_list(request, course_id):
    from apps.courses.models import CourseStudent
    from django.db.models import Count, Q as Qm
    course = get_mentor_course(request.user, course_id)
    course_students = CourseStudent.objects.filter(course=course).select_related('student').order_by('student__full_name')
    agg = course_students.aggregate(
        active=Count('pk', filter=Qm(status='active')),
        left=Count('pk', filter=Qm(status='left')),
        frozen=Count('pk', filter=Qm(status='frozen')),
        graduated=Count('pk', filter=Qm(status='graduated')),
    )
    context = {
        'course': course,
        'course_students': course_students,
        'active_count': agg['active'],
        'left_count': agg['left'],
        'frozen_count': agg['frozen'],
        'graduated_count': agg['graduated'],
        'page_title': 'Студенты',
        'active_menu': 'students',
    }
    return render(request, 'mentor/students/list.html', context)
