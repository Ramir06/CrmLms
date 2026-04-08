from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages


class PermissionRequiredMixin(AccessMixin):
    """
    Mixin для проверки прав доступа в классах представлений
    """
    permission_required = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.permission_required and not request.user.has_permission(self.permission_required):
            messages.error(request, f'У вас нет прав для доступа к этой странице. Требуется право: {self.permission_required}')
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)


class AnyPermissionRequiredMixin(AccessMixin):
    """
    Mixin для проверки наличия хотя бы одного из указанных прав
    """
    permission_required = None  # Может быть строкой или списком
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not self.permission_required:
            return super().dispatch(request, *args, **kwargs)
        
        # Если передано одно право
        if isinstance(self.permission_required, str):
            permissions = [self.permission_required]
        else:
            permissions = self.permission_required
        
        if not any(request.user.has_permission(perm) for perm in permissions):
            messages.error(request, 'У вас нет прав для доступа к этой странице.')
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
