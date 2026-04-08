from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q

from apps.core.mixins import admin_required, super_admin_required
from .models import Organization, OrganizationMember, UserCurrentOrganization
from .forms import OrganizationForm, OrganizationMemberForm
from apps.accounts.models import CustomUser


@login_required
@super_admin_required
def organization_list(request):
    """Список всех организаций (только для суперадмина)."""
    organizations = Organization.objects.all().prefetch_related('members')
    
    context = {
        'organizations': organizations,
        'page_title': 'Организации',
    }
    return render(request, 'admin/organizations/list.html', context)


@login_required
@super_admin_required
def organization_create(request):
    """Создание новой организации."""
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            organization = form.save()
            
            # Создатель становится владельцем организации
            OrganizationMember.objects.create(
                user=request.user,
                organization=organization,
                role='owner'
            )
            
            # Устанавливаем как текущую организацию
            UserCurrentOrganization.objects.update_or_create(
                user=request.user,
                defaults={'organization': organization}
            )
            
            messages.success(request, f'Организация «{organization.name}» создана.')
            return redirect('organizations:detail', pk=organization.pk)
    else:
        form = OrganizationForm()
    
    context = {
        'form': form,
        'page_title': 'Создать организацию',
    }
    return render(request, 'admin/organizations/form.html', context)


@login_required
def organization_detail(request, pk):
    """Детальная информация об организации."""
    organization = get_object_or_404(Organization, pk=pk)
    
    # Проверяем доступ
    if not request.user.is_superuser:
        try:
            member = OrganizationMember.objects.get(
                user=request.user, 
                organization=organization
            )
        except OrganizationMember.DoesNotExist:
            messages.error(request, 'У вас нет доступа к этой организации.')
            return redirect('organizations:my_organizations')
    
    members = organization.members.select_related('user').all()
    
    context = {
        'organization': organization,
        'members': members,
        'page_title': organization.name,
    }
    return render(request, 'admin/organizations/detail.html', context)


@login_required
@super_admin_required
def organization_edit(request, pk):
    """Редактирование организации."""
    organization = get_object_or_404(Organization, pk=pk)
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные организации обновлены.')
            return redirect('organizations:detail', pk=organization.pk)
    else:
        form = OrganizationForm(instance=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'page_title': f'Редактировать {organization.name}',
    }
    return render(request, 'admin/organizations/form.html', context)


@login_required
@admin_required
def edit_current(request):
    """Редактирование текущей организации пользователя."""
    try:
        current_org = UserCurrentOrganization.objects.get(user=request.user).organization
    except UserCurrentOrganization.DoesNotExist:
        messages.error(request, 'У вас нет текущей организации.')
        return redirect('organizations:my_organizations')
    
    # Проверяем права доступа
    if not request.user.is_superuser and request.user.role != 'superadmin':
        member = OrganizationMember.objects.filter(organization=current_org, user=request.user).first()
        if not member or member.role not in ['owner', 'admin']:
            messages.error(request, 'У вас нет прав для редактирования этой организации.')
            return redirect('organizations:detail', pk=current_org.pk)
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=current_org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные организации обновлены.')
            return redirect('organizations:detail', pk=current_org.pk)
    else:
        form = OrganizationForm(instance=current_org)
    
    context = {
        'form': form,
        'organization': current_org,
        'page_title': f'Редактировать {current_org.name}',
    }
    return render(request, 'admin/organizations/form.html', context)


@login_required
@super_admin_required
def organization_delete(request, pk):
    """Удаление организации."""
    organization = get_object_or_404(Organization, pk=pk)
    
    if request.method == 'POST':
        name = organization.name
        organization.delete()
        messages.success(request, f'Организация «{name}» удалена.')
        return redirect('organizations:list')
    
    context = {
        'organization': organization,
        'page_title': 'Удалить организацию',
    }
    return render(request, 'admin/organizations/confirm_delete.html', context)


@login_required
def switch_organization(request, pk):
    """Переключение между организациями."""
    organization = get_object_or_404(Organization, pk=pk)
    
    # Проверяем доступ
    if not request.user.is_superuser:
        has_access = False
        
        # Проверяем через OrganizationMember
        try:
            OrganizationMember.objects.get(
                user=request.user, 
                organization=organization
            )
            has_access = True
        except OrganizationMember.DoesNotExist:
            pass
        
        # Проверяем через StaffOrganizationAccess для персонала
        if not has_access and request.user.role in ('admin', 'manager'):
            try:
                from .models import StaffMember, StaffOrganizationAccess
                staff_member = StaffMember.objects.get(user=request.user)
                StaffOrganizationAccess.objects.get(
                    staff_member=staff_member,
                    organization=organization,
                    is_active=True
                )
                has_access = True
            except (StaffMember.DoesNotExist, StaffOrganizationAccess.DoesNotExist):
                pass
        
        if not has_access:
            messages.error(request, 'У вас нет доступа к этой организации.')
            return redirect('organizations:my_organizations')
    
    # Обновляем текущую организацию
    UserCurrentOrganization.objects.update_or_create(
        user=request.user,
        defaults={'organization': organization}
    )
    
    messages.success(request, f'Переключились на организацию «{organization.name}».')
    
    # Перенаправляем в зависимости от роли
    if request.user.role == 'manager':
        return redirect('manager:dashboard')
    else:
        return redirect('dashboard:index')


@login_required
def my_organizations(request):
    """Мои организации."""
    if request.user.is_superuser:
        # Суперадмин видит все организации
        organizations = Organization.objects.all()
        can_create = True
    elif request.user.role in ('admin', 'manager'):
        # Админ и менеджер видят организации через StaffOrganizationAccess
        try:
            from .models import StaffMember, StaffOrganizationAccess
            staff_member = StaffMember.objects.get(user=request.user)
            organizations = Organization.objects.filter(
                staff_access__staff_member=staff_member,
                staff_access__is_active=True
            ).distinct()
            can_create = False
        except StaffMember.DoesNotExist:
            # Если не является персоналом, ищем через members
            organizations = Organization.objects.filter(
                members__user=request.user,
                members__is_active=True
            ).distinct()
            can_create = False
    else:
        # Обычный пользователь видит только свои организации
        organizations = Organization.objects.filter(
            members__user=request.user,
            members__is_active=True
        ).distinct()
        can_create = False
    
    # Текущая организация
    try:
        current_org = UserCurrentOrganization.objects.get(user=request.user).organization
    except UserCurrentOrganization.DoesNotExist:
        current_org = None
    
    context = {
        'organizations': organizations,
        'current_organization': current_org,
        'can_create': can_create,
        'page_title': 'Мои организации',
    }
    return render(request, 'admin/organizations/my_organizations.html', context)
