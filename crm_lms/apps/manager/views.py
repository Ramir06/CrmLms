from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.dashboard.views import manager_dashboard


@login_required
def dashboard_index(request):
    """Дашборд менеджера - перенаправление на основной дашборд"""
    return manager_dashboard(request)


@login_required
def test_dashboard(request):
    """Тестовый дашборд для проверки работы"""
    return render(request, 'manager/dashboard/test.html')
