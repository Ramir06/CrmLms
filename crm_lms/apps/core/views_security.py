from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.db import models
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

from apps.core.auth_backends import (
    is_account_locked, 
    get_account_lock_info, 
    unlock_account,
    get_failed_attempts_count
)
from apps.core.models_security import AccountLock, FailedLoginAttempt

User = get_user_model()


@login_required
def account_lock_list(request):
    """Список заблокированных аккаунтов (только для админов)"""
    if not request.user.role in ('admin', 'superadmin'):
        messages.error(request, 'Access denied')
        return redirect('dashboard:index')
    
    locks = AccountLock.objects.filter(is_active=True).select_related('user').order_by('-locked_at')
    
    # Поиск
    search = request.GET.get('search', '')
    if search:
        locks = locks.filter(user__username__icontains=search)
    
    # Пагинация
    paginator = Paginator(locks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_locked': locks.count(),
    }
    return render(request, 'admin/security/account_lock_list.html', context)


@login_required
def account_lock_detail(request, user_id):
    """Детальная информация о блокировке аккаунта"""
    if not request.user.role in ('admin', 'superadmin'):
        messages.error(request, 'Access denied')
        return redirect('dashboard:index')
    
    user = get_object_or_404(User, id=user_id)
    lock_info = get_account_lock_info(user)
    failed_attempts = FailedLoginAttempt.objects.filter(username=user.username).order_by('-timestamp')[:10]
    
    context = {
        'target_user': user,
        'lock_info': lock_info,
        'failed_attempts': failed_attempts,
        'is_locked': is_account_locked(user),
        'failed_count': get_failed_attempts_count(user.username),
    }
    return render(request, 'admin/security/account_lock_detail.html', context)


@login_required
@require_POST
def unlock_account_view(request, user_id):
    """Разблокировать аккаунт"""
    if not request.user.role in ('admin', 'superadmin'):
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    user = get_object_or_404(User, id=user_id)
    
    if unlock_account(user):
        messages.success(request, f'Account {user.username} has been unlocked')
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Account is not locked'})


@login_required
def failed_attempts_list(request):
    """Список неудачных попыток входа"""
    if not request.user.role in ('admin', 'superadmin'):
        messages.error(request, 'Access denied')
        return redirect('dashboard:index')
    
    attempts = FailedLoginAttempt.objects.all().order_by('-timestamp')
    
    # Фильтры
    search = request.GET.get('search', '')
    if search:
        attempts = attempts.filter(username__icontains=search)
    
    date_from = request.GET.get('date_from')
    if date_from:
        attempts = attempts.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        attempts = attempts.filter(timestamp__date__lte=date_to)
    
    # Пагинация
    paginator = Paginator(attempts, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'total_attempts': attempts.count(),
    }
    return render(request, 'admin/security/failed_attempts_list.html', context)


@login_required
def security_dashboard(request):
    """Дашборд безопасности"""
    if not request.user.role in ('admin', 'superadmin'):
        messages.error(request, 'Access denied')
        return redirect('dashboard:index')
    
    # Статистика
    total_locked = AccountLock.objects.filter(is_active=True).count()
    recent_locks = AccountLock.objects.filter(is_active=True).order_by('-locked_at')[:5]
    recent_attempts = FailedLoginAttempt.objects.order_by('-timestamp')[:10]
    
    # Попытки за последние 24 часа
    yesterday = timezone.now() - timedelta(days=1)
    recent_failed = FailedLoginAttempt.objects.filter(timestamp__gte=yesterday).count()
    
    # Самые активные IP адреса
    top_ips = FailedLoginAttempt.objects.filter(
        timestamp__gte=yesterday
    ).values('ip_address').annotate(
        count=models.Count('ip_address')
    ).order_by('-count')[:10]
    
    context = {
        'total_locked': total_locked,
        'recent_locks': recent_locks,
        'recent_attempts': recent_attempts,
        'recent_failed': recent_failed,
        'top_ips': top_ips,
    }
    return render(request, 'admin/security/security_dashboard.html', context)


@login_required
@require_POST
def clear_failed_attempts(request, username):
    """Очистить неудачные попытки для пользователя"""
    if not request.user.role in ('admin', 'superadmin'):
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    count = FailedLoginAttempt.objects.filter(username=username).delete()[0]
    return JsonResponse({'success': True, 'cleared': count})
