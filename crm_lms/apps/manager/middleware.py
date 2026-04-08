from django.shortcuts import redirect
from django.conf import settings


class ManagerRedirectMiddleware:
    """
    Middleware для перенаправления менеджеров на их дашборд
    вместо админской панели, но с доступом к нужным разделам
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Если пользователь аутентифицирован и это менеджер
        if request.user.is_authenticated and request.user.role == 'manager':
            # Запрещенные URL для менеджеров (только настройки)
            forbidden_urls = [
                '/admin/settings/',
                '/admin/reports/',
                '/admin/finance/',
                '/admin/salaries/',
                '/django-admin/',
            ]
            
            # Если пытается попасть в запрещенную админскую секцию
            if any(request.path.startswith(url) for url in forbidden_urls):
                return redirect('manager:dashboard')
            
            # Если менеджер пытается попасть на дашборд админки, перенаправляем на менеджерский
            if request.path.startswith('/admin/') and request.path == '/admin/':
                return redirect('manager:dashboard')
        
        return response
