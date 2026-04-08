from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.db.models import Q

from apps.core.mixins import super_admin_required
from .models import Organization, StaffMember, StaffOrganizationAccess
from .forms_superadmin_staff import SuperAdminStaffCreateForm

User = get_user_model()


@login_required
@super_admin_required
def superadmin_organizations(request):
    """Управление организациями для суперадмина"""
    organizations = Organization.objects.all().prefetch_related('members', 'staff_access')
    
    context = {
        'organizations': organizations,
        'page_title': 'Управление организациями',
        'menu_position': 'organizations'
    }
    return render(request, 'admin/organizations/superadmin_organizations.html', context)


@login_required
@super_admin_required
def superadmin_organization_detail(request, pk):
    """Детальная информация об организации с участниками"""
    organization = get_object_or_404(
        Organization.objects.prefetch_related('members__user', 'staff_access__staff_member__user'),
        pk=pk
    )
    
    # Получаем всех участников (через members и staff_access)
    members = []
    
    # Обычные участники
    for member in organization.members.filter(is_active=True):
        members.append({
            'type': 'member',
            'user': member.user,
            'joined_at': member.joined_at,
            'is_active': member.is_active
        })
    
    # Персонал
    for staff_access in organization.staff_access.filter(is_active=True):
        members.append({
            'type': 'staff',
            'user': staff_access.staff_member.user,
            'role': staff_access.staff_member.user.role,
            'joined_at': staff_access.granted_at,
            'is_active': staff_access.is_active,
            'staff_member': staff_access.staff_member
        })
    
    # Сортируем по дате присоединения
    members.sort(key=lambda x: x['joined_at'], reverse=True)
    
    context = {
        'organization': organization,
        'members': members,
        'page_title': f'Участники организации: {organization.name}',
        'menu_position': 'organizations'
    }
    return render(request, 'admin/organizations/superadmin_organization_detail.html', context)


@login_required
@super_admin_required
def superadmin_create_staff(request, org_pk):
    """Создание персонала для конкретной организации"""
    organization = get_object_or_404(Organization, pk=org_pk)
    
    if request.method == 'POST':
        form = SuperAdminStaffCreateForm(request.POST, request.FILES)
        # Устанавливаем текущую организацию как выбранную по умолчанию
        form.initial['organizations'] = [organization]
        # Передаем текущего пользователя в форму для автоматического добавления в мультиаккаунты
        form.current_user = request.user
        
        if form.is_valid():
            try:
                staff_member = form.save()
                messages.success(
                    request, 
                    f'Персонал {staff_member.user.get_display_name()} успешно создан и имеет доступ к {form.cleaned_data["organizations"].count()} организациям'
                )
                return redirect('organizations:superadmin_organization_detail', pk=org_pk)
            except Exception as e:
                messages.error(request, f'Ошибка при создании персонала: {str(e)}')
                print(f"Error creating staff: {e}")  # Отладка
        else:
            # Добавляем ошибки формы в сообщения для отладки
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Ошибка в поле "{field}": {error}')
            print(f"Form errors: {form.errors}")  # Отладка
    else:
        form = SuperAdminStaffCreateForm(initial={'organizations': [organization]})
        # Передаем текущего пользователя в форму
        form.current_user = request.user
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': f'Создание персонала для {organization.name}',
        'menu_position': 'organizations'
    }
    return render(request, 'admin/organizations/superadmin_create_staff.html', context)


@login_required
@super_admin_required
def superadmin_toggle_user(request, pk, org_pk):
    """Блокировка/разблокировка пользователя"""
    user = get_object_or_404(User, pk=pk)
    organization = get_object_or_404(Organization, pk=org_pk)
    
    user.is_active = not user.is_active
    user.save()
    
    action = "разблокирован" if user.is_active else "заблокирован"
    messages.success(request, f'Пользователь {user.get_display_name()} {action}.')
    
    return redirect('organizations:superadmin_organization_detail', pk=org_pk)
