from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import SystemSetting


class MaintenanceModeMiddleware:
    """Middleware to check if maintenance mode is enabled."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled
        if SystemSetting.is_maintenance_mode():
            # Allow access to admin URLs and settings
            admin_paths = ['/admin/', '/admin/settings/', '/django-admin/']
            
            # Allow access if user is authenticated and is admin/superadmin
            if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role in ('admin', 'superadmin'):
                return self.get_response(request)
            
            # Allow access to admin URLs (for login page)
            if any(request.path.startswith(path) for path in admin_paths):
                return self.get_response(request)
            
            # Allow access to login, logout and static files
            if request.path in ['/login/', '/logout/'] or request.path.startswith('/static/') or request.path.startswith('/media/'):
                return self.get_response(request)
            
            # Show maintenance page for everyone else
            return render(request, 'admin/settings/maintenance.html')
        
        return self.get_response(request)
