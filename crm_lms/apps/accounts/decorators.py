from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def permission_required(permission):
    """
    Декоратор для проверки прав доступа пользователя
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_permission(permission):
                messages.error(request, f'У вас нет прав для выполнения этого действия. Требуется право: {permission}')
                return redirect('dashboard:index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def any_permission_required(permissions):
    """
    Декоратор для проверки наличия хотя бы одного из указанных прав
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not any(request.user.has_permission(perm) for perm in permissions):
                messages.error(request, 'У вас нет прав для доступа к этой странице.')
                return redirect('dashboard:index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def role_required(roles):
    """
    Декоратор для проверки роли пользователя
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_superuser:
                user_role = request.user.custom_role.name if request.user.custom_role else request.user.role
                if user_role not in roles:
                    messages.error(request, f'Доступ разрешен только для ролей: {", ".join(roles)}')
                    return redirect('dashboard:index')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
