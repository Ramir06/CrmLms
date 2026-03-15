from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class AdminRequiredMixin(LoginRequiredMixin):
    """Allow access only to admin and superadmin users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ('admin', 'superadmin'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class MentorRequiredMixin(LoginRequiredMixin):
    """Allow access only to mentor users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in ('mentor', 'admin', 'superadmin'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(LoginRequiredMixin):
    """Allow access only to superadmin users."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != 'superadmin':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def admin_required(view_func):
    """Decorator for admin-only views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role not in ('admin', 'superadmin'):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def mentor_required(view_func):
    """Decorator for mentor-only views."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role not in ('mentor', 'admin', 'superadmin'):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
