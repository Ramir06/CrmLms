from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from .models import TicketTariff


@staff_member_required
def get_tariff_data(request, tariff_id):
    """Получение данных тарифа для редактирования"""
    try:
        tariff = TicketTariff.objects.get(id=tariff_id)
        
        return JsonResponse({
            'id': tariff.id,
            'title': tariff.title,
            'lessons_count': tariff.lessons_count,
            'price_per_lesson': float(tariff.price_per_lesson),
            'total_price': float(tariff.total_price),
            'description': tariff.description,
            'is_active': tariff.is_active,
            'created_at': tariff.created_at.isoformat(),
            'updated_at': tariff.updated_at.isoformat()
        })
    except TicketTariff.DoesNotExist:
        return JsonResponse({
            'error': 'Тариф не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
