from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .models import CourseStudent, TicketTariff, TicketBalance, TicketTransaction
from apps.students.models import Student
from apps.accounts.models import CustomUser


@staff_member_required
def student_details_api(request, cs_id):
    """API для получения деталей студента"""
    try:
        cs = get_object_or_404(CourseStudent, id=cs_id)
        student = cs.student
        course = cs.course
        
        # Получаем баланс талонов
        balance = getattr(cs, 'ticket_balance', None)
        remaining_tickets = balance.remaining_tickets if balance else 0
        total_tickets = balance.total_tickets if balance else 0
        
        # Определяем расписание
        schedule = course.get_days_display_short()
        if course.lesson_start_time and course.lesson_end_time:
            schedule += f" {course.lesson_start_time.strftime('%H:%M')}-{course.lesson_end_time.strftime('%H:%M')}"
        
        data = {
            'cs_id': cs.id,
            'student_name': student.full_name,
            'has_account': student.user_account is not None,
            'course_title': course.title,
            'is_unlimited_course': course.is_unlimited,
            'schedule': schedule,
            'remaining_tickets': remaining_tickets,
            'total_tickets': total_tickets,
            'status': cs.get_status_display()
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
def tariffs_api(request):
    """API для получения списка тарифов"""
    try:
        tariffs = TicketTariff.objects.filter(is_active=True).order_by('lessons_count')
        data = []
        
        for tariff in tariffs:
            data.append({
                'id': tariff.id,
                'title': tariff.title,
                'lessons_count': tariff.lessons_count,
                'price_per_lesson': float(tariff.price_per_lesson),
                'total_price': float(tariff.total_price)
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
def tariff_detail_api(request, tariff_id):
    """API для получения деталей тарифа"""
    try:
        tariff = get_object_or_404(TicketTariff, id=tariff_id, is_active=True)
        
        data = {
            'id': tariff.id,
            'title': tariff.title,
            'lessons_count': tariff.lessons_count,
            'price_per_lesson': float(tariff.price_per_lesson),
            'total_price': float(tariff.total_price)
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
def add_tickets_api(request):
    """API для добавления талонов студенту"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        cs_id = request.POST.get('course_student_id')
        tariff_id = request.POST.get('tariff_id')
        issue_date = request.POST.get('issue_date')
        
        if not all([cs_id, tariff_id, issue_date]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Получаем объекты
        cs = get_object_or_404(CourseStudent, id=cs_id)
        tariff = get_object_or_404(TicketTariff, id=tariff_id, is_active=True)
        
        # Проверяем что курс бесконечный
        if not cs.course.is_unlimited:
            return JsonResponse({'error': 'Tickets can only be added to unlimited courses'}, status=400)
        
        # Парсим дату
        from datetime import datetime
        try:
            parsed_date = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        # Создаем или получаем баланс талонов
        balance, created = TicketBalance.objects.get_or_create(
            enrollment=cs,
            defaults={
                'total_tickets': 0,
                'used_tickets': 0
            }
        )
        
        # Добавляем транзакцию
        transaction = TicketTransaction.objects.create(
            enrollment=cs,
            transaction_type='add',
            quantity=tariff.lessons_count,
            price_per_ticket=tariff.price_per_lesson,
            comment=f'Добавлено по тарифу "{tariff.title}"',
            created_by=request.user
        )
        
        # Обновляем баланс
        balance.total_tickets += tariff.lessons_count
        balance.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Успешно добавлено {tariff.lessons_count} талонов',
            'new_balance': balance.remaining_tickets
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def ticket_history_api(request, cs_id):
    """API для получения истории талонов студента"""
    try:
        cs = get_object_or_404(CourseStudent, id=cs_id)
        
        transactions = cs.ticket_transactions.all().order_by('-created_at')
        data = []
        
        for transaction in transactions:
            data.append({
                'id': transaction.id,
                'type': transaction.get_transaction_type_display(),
                'quantity': transaction.quantity,
                'price_per_ticket': float(transaction.price_per_ticket) if transaction.price_per_ticket else None,
                'comment': transaction.comment,
                'created_at': transaction.created_at.strftime('%d.%m.%Y %H:%M'),
                'created_by': transaction.created_by.get_display_name() if transaction.created_by else 'System'
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
