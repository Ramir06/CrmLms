from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from apps.core.mixins import admin_required
from .models import LeadStatus, LeadSource, Lead
from .forms import LeadStatusForm, LeadSourceForm


@login_required
@admin_required
@require_POST
def lead_status_delete_with_leads(request, pk):
    """Удаление статуса лида вместе со всеми лидами"""
    try:
        status = get_object_or_404(LeadStatus, pk=pk)
        
        # Сначала удаляем всех лидов с этим статусом
        deleted_leads_count = Lead.objects.filter(custom_status=status).delete()[0]
        
        # Затем удаляем сам статус
        status_name = status.name
        status.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Статус "{status_name}" и {deleted_leads_count} лид(а/ов) успешно удалены'
        })
        
    except LeadStatus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Статус не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при удалении: {str(e)}'
        }, status=500)


@login_required
@admin_required
@require_POST
def lead_source_delete_with_leads(request, pk):
    """Удаление источника лида вместе со всеми лидами"""
    try:
        source = get_object_or_404(LeadSource, pk=pk)
        
        # Сначала удаляем всех лидов с этим источником
        deleted_leads_count = Lead.objects.filter(custom_source=source).delete()[0]
        
        # Затем удаляем сам источник
        source_name = source.name
        source.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Источник "{source_name}" и {deleted_leads_count} лид(а/ов) успешно удалены'
        })
        
    except LeadSource.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Источник не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при удалении: {str(e)}'
        }, status=500)


@login_required
@admin_required
def lead_status_list(request):
    """Список статусов лидов"""
    statuses = LeadStatus.objects.all().order_by('order', 'name')
    
    context = {
        'statuses': statuses,
        'page_title': 'Статусы лидов'
    }
    return render(request, 'admin/leads/settings/status_list.html', context)


@login_required
@admin_required
def lead_status_create(request):
    """Создание нового статуса лида"""
    if request.method == 'POST':
        form = LeadStatusForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статус успешно создан')
            return redirect('leads:lead_status_list')
    else:
        form = LeadStatusForm()
    
    context = {
        'form': form,
        'page_title': 'Создать статус лида'
    }
    return render(request, 'admin/leads/settings/status_form.html', context)


@login_required
@admin_required
def lead_status_edit(request, pk):
    """Редактирование статуса лида"""
    status = get_object_or_404(LeadStatus, pk=pk)
    
    if request.method == 'POST':
        form = LeadStatusForm(request.POST, request.FILES, instance=status)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статус успешно обновлен')
            return redirect('leads:lead_status_list')
    else:
        form = LeadStatusForm(instance=status)
    
    context = {
        'form': form,
        'status': status,
        'page_title': f'Редактировать статус: {status.name}'
    }
    return render(request, 'admin/leads/settings/status_form.html', context)


@login_required
@admin_required
@require_POST
def lead_status_delete(request, pk):
    """Удаление статуса лида"""
    try:
        status = get_object_or_404(LeadStatus, pk=pk)
        
        # Проверяем, используется ли статус
        leads_count = status.lead_set.count()
        print(f"Status {status.name} has {leads_count} leads")  # Отладка
        
        if leads_count > 0:
            return JsonResponse({
                'success': False,
                'error': f'Нельзя удалить статус "{status.name}"! Он используется {leads_count} лидами. Сначала измените статус у этих лидов.'
            })
        
        status.delete()
        return JsonResponse({'success': True})
        
    except LeadStatus.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Статус не найден'
        }, status=404)
    except Exception as e:
        print(f"Error deleting status: {e}")  # Отладка
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при удалении: {str(e)}'
        }, status=500)


@login_required
@admin_required
def lead_source_list(request):
    """Список источников лидов"""
    sources = LeadSource.objects.all().order_by('order', 'name')
    
    context = {
        'sources': sources,
        'page_title': 'Источники лидов'
    }
    return render(request, 'admin/leads/settings/source_list.html', context)


@login_required
@admin_required
def lead_source_create(request):
    """Создание нового источника лида"""
    if request.method == 'POST':
        form = LeadSourceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Источник успешно создан')
            return redirect('leads:lead_source_list')
    else:
        form = LeadSourceForm()
    
    context = {
        'form': form,
        'page_title': 'Создать источник лида'
    }
    return render(request, 'admin/leads/settings/source_form.html', context)


@login_required
@admin_required
def lead_source_edit(request, pk):
    """Редактирование источника лида"""
    source = get_object_or_404(LeadSource, pk=pk)
    
    if request.method == 'POST':
        form = LeadSourceForm(request.POST, request.FILES, instance=source)
        if form.is_valid():
            form.save()
            messages.success(request, 'Источник успешно обновлен')
            return redirect('leads:lead_source_list')
    else:
        form = LeadSourceForm(instance=source)
    
    context = {
        'form': form,
        'source': source,
        'page_title': f'Редактировать источник: {source.name}'
    }
    return render(request, 'admin/leads/settings/source_form.html', context)


@login_required
@admin_required
@require_POST
def lead_source_delete(request, pk):
    """Удаление источника лида"""
    try:
        source = get_object_or_404(LeadSource, pk=pk)
        
        # Проверяем, используется ли источник
        leads_count = source.lead_set.count()
        print(f"Source {source.name} has {leads_count} leads")  # Отладка
        
        if leads_count > 0:
            return JsonResponse({
                'success': False,
                'error': f'Нельзя удалить источник "{source.name}"! Он используется {leads_count} лидами. Сначала удалите или измените источник у этих лидов.'
            })
        
        source.delete()
        return JsonResponse({'success': True})
        
    except LeadSource.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Источник не найден'
        }, status=404)
    except Exception as e:
        print(f"Error deleting source: {e}")  # Отладка
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при удалении: {str(e)}'
        }, status=500)


@login_required
@admin_required
def settings_dashboard(request):
    """Панель настроек лидов"""
    context = {
        'page_title': 'Настройки лидов'
    }
    return render(request, 'admin/leads/settings/dashboard.html', context)
