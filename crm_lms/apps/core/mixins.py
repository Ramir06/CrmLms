from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.core.cache import cache
from apps.settings.models import SystemSetting
import json


class AdminRequiredMixin(LoginRequiredMixin):
    """Allow access only to admin, superadmin, and manager users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ('admin', 'superadmin', 'manager'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class MentorRequiredMixin(LoginRequiredMixin):
    """Allow access only to mentor, admin, superadmin, and manager users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ('mentor', 'admin', 'superadmin', 'manager'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(LoginRequiredMixin):
    """Allow access only to superadmin users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SettingsRequiredMixin(LoginRequiredMixin):
    """Allow access only to superadmin and admin users for settings."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ('superadmin', 'admin'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def super_admin_required(view_func):
    """Decorator for superadmin-only views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator for admin-only views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Проверяем права доступа через кастомные роли или стандартные роли
        if not request.user.has_permission('view_mentors'):
            raise PermissionDenied("У вас нет прав для просмотра менторов")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def students_required(view_func):
    """Decorator for students views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Проверяем права доступа через кастомные роли или стандартные роли
        if not request.user.has_permission('view_students'):
            raise PermissionDenied("У вас нет прав для просмотра студентов")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def courses_required(view_func):
    """Decorator for courses views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Проверяем права доступа через кастомные роли или стандартные роли
        if not request.user.has_permission('view_courses'):
            raise PermissionDenied("У вас нет прав для просмотра курсов")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def permission_required(permission):
    """Decorator for views requiring specific permission."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if not request.user.has_permission(permission):
                raise PermissionDenied(f"У вас нет прав для этого действия. Требуется право: {permission}")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def mentor_required(view_func):
    """Decorator for mentor-only views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role not in ('mentor', 'admin', 'superadmin', 'manager'):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def get_menu_position():
    """Возвращает положение меню из настроек."""
    # Сначала пробуем получить из кэша
    position = cache.get('menu_position')
    if position is not None:
        return position
    
    # Если в кэше нет, получаем из базы
    position = SystemSetting.get_value('menu_position', 'left')
    cache.set('menu_position', position, timeout=3600)
    return position


def get_student_form_fields():
    """Возвращает список полей для формы создания студента."""
    # Сначала пробуем получить из кэша
    fields = cache.get('student_form_fields')
    if fields is not None:
        return fields
    
    # Если в кэше нет, получаем из базы
    student_fields_json = SystemSetting.get_value('student_form_fields', '["login", "password", "email"]')
    try:
        fields = json.loads(student_fields_json)
    except json.JSONDecodeError:
        fields = ['login', 'password', 'email']
    
    # Сохраняем в кэш
    cache.set('student_form_fields', fields, timeout=3600)
    return fields


class SystemSettingsMixin:
    """Миксин для добавления системных настроек в контекст."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu_position'] = get_menu_position()
        context['student_form_fields'] = get_student_form_fields()
        
        # Добавляем текущую организацию
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            context['current_organization'] = get_current_organization(self.request.user)
        
        return context


def get_current_organization(user):
    """Возвращает текущую организацию пользователя."""
    from apps.organizations.models import UserCurrentOrganization, Organization, StaffMember, StaffOrganizationAccess
    
    try:
        current_org = UserCurrentOrganization.objects.get(user=user).organization
        return current_org
    except UserCurrentOrganization.DoesNotExist:
        # Если нет текущей организации, пытаемся найти первую доступную
        if user.is_superuser:
            # Суперадмин может видеть все организации, но не выбираем случайную
            # Возвращаем None чтобы требовать выбора
            return None
        elif user.role in ('admin', 'manager'):
            # Админ и менеджер видят организации через StaffOrganizationAccess
            try:
                staff_member = StaffMember.objects.get(user=user)
                org = Organization.objects.filter(
                    staff_access__staff_member=staff_member,
                    staff_access__is_active=True
                ).first()
            except StaffMember.DoesNotExist:
                # Если не является персоналом, ищем через members
                org = Organization.objects.filter(
                    members__user=user,
                    members__is_active=True
                ).first()
        else:
            # Обычный пользователь видит только свои организации
            org = Organization.objects.filter(
                members__user=user,
                members__is_active=True
            ).first()
        
        if org:
            # Устанавливаем как текущую
            UserCurrentOrganization.objects.create(user=user, organization=org)
            return org
    
    return None


def organization_context(view_func):
    """Декоратор для автоматического добавления текущей организации в контекст."""
    def wrapper(request, *args, **kwargs):
        # Добавляем текущую организацию в request для использования в шаблонах
        if request.user.is_authenticated:
            request.current_organization = get_current_organization(request.user)
        
        # Вызываем оригинальную функцию
        response = view_func(request, *args, **kwargs)
        
        # Если это HttpResponse с контекстом, добавляем current_organization
        if hasattr(response, 'context_data') and request.user.is_authenticated:
            response.context_data['current_organization'] = request.current_organization
        # Для простых render responses также добавляем в контекст
        elif hasattr(response, 'context') and request.user.is_authenticated:
            response.context['current_organization'] = request.current_organization
        
        return response
    return wrapper
