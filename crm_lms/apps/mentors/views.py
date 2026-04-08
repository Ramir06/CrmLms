from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from apps.core.mixins import admin_required, get_current_organization
from apps.accounts.models import CustomUser
from apps.accounts.forms import CreateUserForm
from .models import MentorProfile
from .forms import MentorProfileForm
from .kpi_utils import calculate_mentor_kpi, update_mentor_kpi, get_kpi_status_display


@login_required
@admin_required
def mentor_list(request):
    # Фильтруем менторов по текущей организации
    current_org = get_current_organization(request.user)
    mentors = MentorProfile.objects.filter(organization=current_org) if current_org else MentorProfile.objects.none()
    mentors = mentors.select_related('user').filter(is_active=True)
    search = request.GET.get('q', '')
    
    # Фильтры
    if search:
        mentors = mentors.filter(
            Q(user__full_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(specialization__icontains=search)
        )
    
    if request.GET.get('status') == 'active':
        mentors = mentors.filter(is_active=True)
    elif request.GET.get('status') == 'inactive':
        mentors = mentors.filter(is_active=False)
        
    if request.GET.get('kpi_status'):
        mentors = mentors.filter(kpi_status=request.GET.get('kpi_status'))
    
    context = {
        'mentors': mentors, 
        'search': search, 
        'page_title': 'Менторы - KPI'
    }
    return render(request, 'admin/mentors/list_simple.html', context)


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
            # Устанавливаем организацию
            current_org = get_current_organization(request.user)
            if current_org:
                profile.organization = current_org
                
                # Добавляем ментора как участника организации
                from apps.organizations.models import OrganizationMember, UserCurrentOrganization
                member, created = OrganizationMember.objects.get_or_create(
                    user=user,
                    organization=current_org,
                    defaults={'role': 'member'}
                )
                if created:
                    print(f"✅ Ментор {user.get_display_name()} добавлен в организацию {current_org.name}")
                
                # Устанавливаем текущую организацию для ментора
                user_current_org, created = UserCurrentOrganization.objects.get_or_create(
                    user=user,
                    defaults={'organization': current_org}
                )
                if not created:
                    user_current_org.organization = current_org
                    user_current_org.save()
                    
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
    # Фильтруем ментора по организации пользователя
    current_org = get_current_organization(request.user)
    mentor_queryset = MentorProfile.objects.filter(organization=current_org) if current_org else MentorProfile.objects.none()
    profile = get_object_or_404(mentor_queryset, pk=pk)
    courses = profile.user.mentor_courses.filter(is_archived=False)
    from apps.salaries.models import SalaryAccrual
    salary_history = SalaryAccrual.objects.filter(mentor=profile.user).order_by('-month')[:12]
    context = {
        'profile': profile,
        'courses': courses,
        'salary_history': salary_history,
        'page_title': f'{profile.get_display_name()} - KPI',
    }
    return render(request, 'admin/mentors/detail_with_kpi.html', context)


@login_required
@admin_required
def mentor_block(request, pk):
    # Фильтруем ментора по организации пользователя
    current_org = get_current_organization(request.user)
    mentor_queryset = MentorProfile.objects.filter(organization=current_org) if current_org else MentorProfile.objects.none()
    profile = get_object_or_404(mentor_queryset, pk=pk)
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


# KPI API Views
@require_http_methods(["GET"])
def mentor_kpi_api(request, mentor_id):
    """
    API endpoint для получения KPI ментора
    GET /api/mentors/{id}/kpi/
    """
    try:
        # Проверяем существование ментора
        mentor = get_object_or_404(
            CustomUser.objects.filter(role='mentor'),
            id=mentor_id
        )
        
        # Получаем KPI данные
        kpi_data = calculate_mentor_kpi(mentor.id)
        
        # Добавляем человекочитаемые статусы
        response_data = {
            'attendance': kpi_data['attendance'],
            'grades': kpi_data['grades'],
            'reviews': kpi_data['reviews'],
            'kpi': kpi_data['kpi'],
            'status': get_kpi_status_display(kpi_data['status']),
            'status_code': kpi_data['status'],
            'mentor_name': mentor.get_display_name(),
            'mentor_email': mentor.email
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Ошибка при расчёте KPI',
            'details': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_mentor_kpi_api(request, mentor_id):
    """
    API endpoint для принудительного обновления KPI ментора
    POST /api/mentors/{id}/kpi/update/
    """
    try:
        # Проверяем существование ментора
        mentor = get_object_or_404(
            CustomUser.objects.filter(role='mentor'),
            id=mentor_id
        )
        
        # Обновляем KPI в базе данных
        kpi_data = update_mentor_kpi(mentor.id)
        
        if kpi_data is None:
            return JsonResponse({
                'error': 'Профиль ментора не найден'
            }, status=404)
        
        response_data = {
            'message': 'KPI успешно обновлён',
            'attendance': kpi_data['attendance'],
            'grades': kpi_data['grades'],
            'reviews': kpi_data['reviews'],
            'kpi': kpi_data['kpi'],
            'status': get_kpi_status_display(kpi_data['status']),
            'status_code': kpi_data['status']
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Ошибка при обновлении KPI',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
def mentors_kpi_list(request):
    """
    API endpoint для получения KPI всех менторов
    GET /api/mentors/kpi/
    """
    try:
        mentors = CustomUser.objects.filter(role='mentor')
        mentors_kpi = []
        
        for mentor in mentors:
            kpi_data = calculate_mentor_kpi(mentor.id)
            mentors_kpi.append({
                'id': mentor.id,
                'name': mentor.get_display_name(),
                'email': mentor.email,
                'kpi': kpi_data['kpi'],
                'status': get_kpi_status_display(kpi_data['status']),
                'status_code': kpi_data['status'],
                'attendance': kpi_data['attendance'],
                'grades': kpi_data['grades'],
                'reviews': kpi_data['reviews']
            })
        
        # Сортируем по KPI убыванию
        mentors_kpi.sort(key=lambda x: x['kpi'], reverse=True)
        
        return JsonResponse({
            'mentors': mentors_kpi,
            'total': len(mentors_kpi)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Ошибка при получении списка KPI',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def my_kpi(request):
    """
    API endpoint для получения KPI текущего пользователя (если он ментор)
    GET /api/my-kpi/
    """
    try:
        if request.user.role != 'mentor':
            return JsonResponse({
                'error': 'Доступ запрещён. Только для менторов.'
            }, status=403)
        
        kpi_data = calculate_mentor_kpi(request.user.id)
        
        response_data = {
            'attendance': kpi_data['attendance'],
            'grades': kpi_data['grades'],
            'reviews': kpi_data['reviews'],
            'kpi': kpi_data['kpi'],
            'status': get_kpi_status_display(kpi_data['status']),
            'status_code': kpi_data['status']
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Ошибка при получении KPI',
            'details': str(e)
        }, status=500)
