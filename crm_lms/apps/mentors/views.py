from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q

from apps.core.mixins import admin_required
from apps.accounts.models import CustomUser
from apps.accounts.forms import CreateUserForm
from .models import MentorProfile
from .forms import MentorProfileForm


@login_required
@admin_required
def mentor_list(request):
    mentors = MentorProfile.objects.select_related('user').filter(is_active=True)
    search = request.GET.get('q', '')
    if search:
        mentors = mentors.filter(
            Q(user__full_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(specialization__icontains=search)
        )
    context = {'mentors': mentors, 'search': search, 'page_title': 'Менторы'}
    return render(request, 'admin/mentors/list.html', context)


@login_required
@admin_required
def mentor_create(request):
    user_form = CreateUserForm(request.POST or None)
    profile_form = MentorProfileForm(request.POST or None)

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'mentor'
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, f'Ментор «{user.get_display_name()}» создан.')
            return redirect('mentors:detail', pk=profile.pk)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'page_title': 'Добавить ментора',
    }
    return render(request, 'admin/mentors/form.html', context)


@login_required
@admin_required
def mentor_detail(request, pk):
    profile = get_object_or_404(MentorProfile, pk=pk)
    courses = profile.user.mentor_courses.filter(is_archived=False)
    from apps.salaries.models import SalaryAccrual
    salary_history = SalaryAccrual.objects.filter(mentor=profile.user).order_by('-month')[:12]
    context = {
        'profile': profile,
        'courses': courses,
        'salary_history': salary_history,
        'page_title': profile.get_display_name(),
    }
    return render(request, 'admin/mentors/detail.html', context)


@login_required
@admin_required
def mentor_block(request, pk):
    profile = get_object_or_404(MentorProfile, pk=pk)
    if request.method == 'POST':
        user = profile.user
        user.is_active = not user.is_active
        user.save()
        if user.is_active:
            messages.success(request, f'Аккаунт «{profile.get_display_name()}» разблокирован.')
        else:
            messages.warning(request, f'Аккаунт «{profile.get_display_name()}» заблокирован.')
    return redirect('mentors:detail', pk=pk)


@login_required
@admin_required
def mentor_reset_password(request, pk):
    profile = get_object_or_404(MentorProfile, pk=pk)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            profile.user.set_password(new_password)
            profile.user.save()
            messages.success(request, f'Пароль для «{profile.get_display_name()}» сброшен.')
        else:
            messages.error(request, 'Введите новый пароль.')
    return redirect('mentors:detail', pk=pk)


@login_required
@admin_required
def mentor_export(request):
    import openpyxl
    from django.utils import timezone

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Менторы'
    ws.append(['ID', 'Имя', 'Email', 'Специализация', 'Тип зарплаты', 'Активен'])
    for m in MentorProfile.objects.select_related('user').all():
        ws.append([
            m.pk, m.user.get_display_name(), m.user.email,
            m.specialization, m.get_salary_type_display(), m.is_active,
        ])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=mentors_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response


@login_required
@admin_required
def mentor_2fa_settings(request):
    try:
        profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.error(request, 'У вас нет профиля ментора.')
        return redirect('mentors:list')
    
    # Временно используем False, т.к. поля нет до миграций
    two_factor_enabled = getattr(profile, 'two_factor_enabled', False)
    
    context = {
        'two_factor_enabled': two_factor_enabled,
        'page_title': '2FA Настройки'
    }
    return render(request, 'admin/2fa.html', context)


@login_required
@admin_required
def enable_2fa(request):
    try:
        profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.error(request, 'У вас нет профиля ментора.')
        return redirect('mentors:2fa_settings')
    
    if request.method == 'POST':
        # Временно не можем включить 2FA без миграций
        messages.warning(request, '2FA временно недоступна до применения миграций.')
        code = profile.send_2fa_code()
        messages.info(request, f'Тестовый код: {code} (только для отладки)')
    
    return redirect('mentors:2fa_settings')


@login_required
@admin_required
def disable_2fa(request):
    try:
        profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.error(request, 'У вас нет профиля ментора.')
        return redirect('mentors:2fa_settings')
    
    if request.method == 'POST':
        # Временно не можем отключить 2FA без миграций
        messages.warning(request, '2FA временно недоступна до применения миграций.')
    
    return redirect('mentors:2fa_settings')


@login_required
@admin_required
def test_2fa(request):
    try:
        profile = request.user.mentor_profile
    except MentorProfile.DoesNotExist:
        messages.error(request, 'У вас нет профиля ментора.')
        return redirect('mentors:2fa_settings')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if profile.verify_2fa_code(code):
            messages.success(request, 'Код подтверждения верный! 2FA работает корректно.')
        else:
            messages.error(request, 'Неверный код. Попробуйте еще раз.')
    
    return redirect('mentors:2fa_settings')
