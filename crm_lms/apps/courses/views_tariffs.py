from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import TicketTariff
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@staff_member_required
def tariffs_list(request):
    """Страница управления тарифами"""
    tariffs = TicketTariff.objects.all().order_by('-created_at')
    
    context = {
        'tariffs': tariffs,
        'title': 'Управление тарифами'
    }
    
    return render(request, 'admin/courses/tariffs_list.html', context)


@require_http_methods(["POST"])
@staff_member_required
def create_tariff(request):
    """Создание нового тарифа"""
    try:
        title = request.POST.get('title')
        lessons_count = int(request.POST.get('lessons_count'))
        price_per_lesson = float(request.POST.get('price_per_lesson'))
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        tariff = TicketTariff.objects.create(
            title=title,
            lessons_count=lessons_count,
            price_per_lesson=price_per_lesson,
            description=description,
            is_active=is_active
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Тариф успешно создан',
            'tariff': {
                'id': tariff.id,
                'title': tariff.title,
                'lessons_count': tariff.lessons_count,
                'price_per_lesson': tariff.price_per_lesson,
                'total_price': tariff.total_price,
                'description': tariff.description,
                'is_active': tariff.is_active,
                'created_at': tariff.created_at.strftime('%d.%m.%Y %H:%M')
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["POST"])
@staff_member_required
def update_tariff(request, tariff_id):
    """Обновление тарифа"""
    try:
        tariff = TicketTariff.objects.get(id=tariff_id)
        
        title = request.POST.get('title')
        lessons_count = int(request.POST.get('lessons_count'))
        price_per_lesson = float(request.POST.get('price_per_lesson'))
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        tariff.title = title
        tariff.lessons_count = lessons_count
        tariff.price_per_lesson = price_per_lesson
        tariff.description = description
        tariff.is_active = is_active
        tariff.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Тариф успешно обновлен',
            'tariff': {
                'id': tariff.id,
                'title': tariff.title,
                'lessons_count': tariff.lessons_count,
                'price_per_lesson': tariff.price_per_lesson,
                'total_price': tariff.total_price,
                'description': tariff.description,
                'is_active': tariff.is_active,
                'updated_at': tariff.updated_at.strftime('%d.%m.%Y %H:%M')
            }
        })
    except TicketTariff.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Тариф не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["POST"])
@staff_member_required
def delete_tariff(request, tariff_id):
    """Удаление тарифа"""
    try:
        tariff = TicketTariff.objects.get(id=tariff_id)
        tariff.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Тариф успешно удален'
        })
    except TicketTariff.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Тариф не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["POST"])
@staff_member_required
def toggle_tariff(request, tariff_id):
    """Включение/выключение тарифа"""
    try:
        tariff = TicketTariff.objects.get(id=tariff_id)
        tariff.is_active = not tariff.is_active
        tariff.save()
        
        status = 'активирован' if tariff.is_active else 'деактивирован'
        
        return JsonResponse({
            'success': True,
            'message': f'Тариф успешно {status}',
            'is_active': tariff.is_active
        })
    except TicketTariff.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Тариф не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
