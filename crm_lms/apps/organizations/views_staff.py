from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.db.models import Q

from apps.core.mixins import super_admin_required
from .models import StaffMember, StaffOrganizationAccess
from .forms_staff import StaffCreationForm, StaffOrganizationAccessForm
from .forms_staff_create import StaffCreateForm


@login_required
@super_admin_required
def staff_create(request):
    """Создание персонала"""
    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            try:
                staff_member = form.save()
                messages.success(
                    request, 
                    f'Персонал {staff_member.user.get_display_name()} успешно создан и имеет доступ к {form.cleaned_data["organizations"].count()} организациям'
                )
                return redirect('organizations:staff_list')
            except Exception as e:
                messages.error(request, f'Ошибка при создании персонала: {str(e)}')
    else:
        form = StaffCreateForm()
    
    context = {
        'form': form,
        'page_title': 'Создание персонала',
        'menu_position': 'organizations'
    }
    return render(request, 'admin/organizations/staff_create_new.html', context)


class StaffListView(LoginRequiredMixin, ListView):
    """Список персонала"""
    model = StaffMember
    template_name = 'admin/organizations/staff_list.html'
    context_object_name = 'staff_members'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = StaffMember.objects.select_related('user', 'created_by').order_by('-created_at')
        
        # Поиск
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Фильтр по роли
        role = self.request.GET.get('role', '')
        if role:
            queryset = queryset.filter(user__role=role)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Персонал'
        context['menu_position'] = 'organizations'
        context['search'] = self.request.GET.get('search', '')
        context['role'] = self.request.GET.get('role', '')
        
        # Статистика
        context['total_staff'] = StaffMember.objects.count()
        context['admin_count'] = StaffMember.objects.filter(user__role='admin').count()
        context['manager_count'] = StaffMember.objects.filter(user__role='manager').count()
        context['superadmin_count'] = StaffMember.objects.filter(user__role='superadmin').count()
        
        return context


@login_required
@super_admin_required
def staff_detail(request, pk):
    """Детальная информация о персонале"""
    staff_member = get_object_or_404(
        StaffMember.objects.select_related('user', 'created_by'),
        pk=pk
    )
    
    # Получаем доступы к организациям
    organization_accesses = StaffOrganizationAccess.objects.filter(
        staff_member=staff_member
    ).select_related('organization', 'granted_by').order_by('-granted_at')
    
    return render(request, 'admin/organizations/staff_detail.html', {
        'staff_member': staff_member,
        'organization_accesses': organization_accesses,
        'page_title': f'Персонал: {staff_member.user.get_display_name()}',
        'menu_position': 'organizations'
    })


@login_required
@super_admin_required
def staff_edit_access(request, pk):
    """Редактирование доступа персонала к организациям"""
    staff_member = get_object_or_404(StaffMember, pk=pk)
    
    if request.method == 'POST':
        form = StaffOrganizationAccessForm(staff_member, request.POST)
        if form.is_valid():
            try:
                form.save(granted_by=request.user)
                messages.success(
                    request,
                    f'Доступы для {staff_member.user.get_display_name()} обновлены'
                )
                return redirect('organizations:staff_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении доступов: {str(e)}')
    else:
        form = StaffOrganizationAccessForm(staff_member)
    
    return render(request, 'admin/organizations/staff_edit_access.html', {
        'form': form,
        'staff_member': staff_member,
        'page_title': f'Редактирование доступов: {staff_member.user.get_display_name()}',
        'menu_position': 'organizations'
    })


@login_required
@super_admin_required
def staff_toggle_active(request, pk):
    """Включение/отключение персонала"""
    staff_member = get_object_or_404(StaffMember, pk=pk)
    user = staff_member.user
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'активирован' if user.is_active else 'деактивирован'
    messages.success(request, f'Персонал {user.get_display_name()} {status}')
    
    return redirect('organizations:staff_list')


@login_required
@super_admin_required
def staff_delete(request, pk):
    """Удаление персонала"""
    staff_member = get_object_or_404(StaffMember, pk=pk)
    user = staff_member.user
    
    if request.method == 'POST':
        user_name = user.get_display_name()
        user.delete()
        messages.success(request, f'Персонал {user_name} удален')
        return redirect('organizations:staff_list')
    
    return render(request, 'admin/organizations/staff_confirm_delete.html', {
        'staff_member': staff_member,
        'page_title': 'Удаление персонала',
        'menu_position': 'organizations'
    })
