from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from apps.core.mixins import admin_required
from apps.core.mixins_organization import get_current_organization, filter_by_organization
from .models import Debt
from apps.students.models import Student
from apps.payments.models import Payment
from apps.settings.models import PaymentMethod
from django.utils import timezone


@login_required
@admin_required
def debt_list(request):
    # Получаем текущую организацию
    current_org = get_current_organization(request.user)
    
    qs = Debt.objects.select_related('student', 'course').filter(status='active')
    
    # Исключаем бесконечные курсы из обычных долгов
    qs = qs.filter(course__is_unlimited=False)
    
    # Фильтруем по организации
    qs = filter_by_organization(qs, current_org)
    
    course_id = request.GET.get('course')
    if course_id:
        qs = qs.filter(course_id=course_id)

    # Разделяем долги по типам
    monthly_debts = qs.filter(debt_type='monthly')
    lesson_debts = qs.filter(debt_type='lesson')
    
    total_debt = qs.aggregate(s=Sum('total_amount'))['s'] or 0
    
    # Получаем информацию о красных занятиях для бесконечных курсов
    ticket_debts = []
    from apps.courses.models import CourseStudent
    from apps.courses.tickets import TicketBalance
    
    # Получаем все записи на бесконечные курсы
    unlimited_enrollments = CourseStudent.objects.filter(
        status='active',
        course__is_unlimited=True
    ).select_related('student', 'course').prefetch_related('ticket_balance')
    
    # Фильтруем по организации
    if current_org:
        unlimited_enrollments = unlimited_enrollments.filter(course__organization=current_org)
    
    print(f"DEBUG: Found {unlimited_enrollments.count()} unlimited enrollments")
    
    for enrollment in unlimited_enrollments:
        try:
            ticket_balance = enrollment.ticket_balance
            if ticket_balance is None:
                print(f"DEBUG: No ticket balance for {enrollment.student.full_name} in {enrollment.course.title}")
                continue
                
            print(f"DEBUG: {enrollment.student.full_name} - remaining: {ticket_balance.remaining_tickets}, total: {ticket_balance.total_tickets}, used: {ticket_balance.used_tickets}")
            
            if ticket_balance.remaining_tickets < 0:
                # У студента есть красные занятия (долг талонов)
                overdue_lessons = abs(ticket_balance.remaining_tickets)
                print(f"DEBUG: Found ticket debt for {enrollment.student.full_name}: {overdue_lessons} overdue lessons")
                ticket_debts.append({
                    'student': enrollment.student,
                    'course': enrollment.course,
                    'enrollment_pk': enrollment.pk,  # Добавляем ID записи на курс
                    'overdue_lessons': overdue_lessons,
                    'total_tickets': ticket_balance.total_tickets,
                    'used_tickets': ticket_balance.used_tickets,
                    'remaining_tickets': ticket_balance.remaining_tickets,
                    'is_ticket_debt': True
                })
        except TicketBalance.DoesNotExist:
            print(f"DEBUG: TicketBalance.DoesNotExist for {enrollment.student.full_name}")
            pass
        except Exception as e:
            print(f"Error processing ticket debt for {enrollment.student.full_name}: {e}")
            pass
    
    # Фильтруем красные занятия по курсу если нужно
    if course_id:
        ticket_debts = [debt for debt in ticket_debts if debt['course'].pk == int(course_id)]
    
    # Получаем способы оплаты для модального окна
    from apps.settings.models import PaymentMethod
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    # Текущий месяц и год
    from django.utils import timezone
    today = timezone.now().date()

    print(f"DEBUG: Final ticket_debts count: {len(ticket_debts)}")
    
    context = {
        'debts': qs,
        'monthly_debts': monthly_debts,
        'lesson_debts': lesson_debts,
        'ticket_debts': ticket_debts,
        'total_debt': total_debt,
        'payment_methods': payment_methods,
        'current_month': today.month,
        'current_year': today.year,
        'page_title': 'Должники',
        'debug_info': {
            'unlimited_enrollments_count': unlimited_enrollments.count(),
            'ticket_debts_count': len(ticket_debts)
        }
    }
    return render(request, 'admin/debts/list.html', context)


@login_required
@admin_required
def debt_export(request):
    import openpyxl
    from django.utils import timezone
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Долги'
    ws.append(['ID', 'Студент', 'Курс', 'Всего', 'Оплачено', 'Долг', 'Статус'])
    for d in Debt.objects.select_related('student', 'course').all():
        ws.append([d.pk, d.student.full_name, d.course.title,
                   float(d.total_amount), float(d.paid_amount),
                   float(d.debt_amount), d.get_status_display()])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=debts_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response


@login_required
@admin_required
def block_student_account(request, debt_id):
    """Блокировать аккаунт студента-должника"""
    debt = get_object_or_404(Debt, pk=debt_id)
    student = debt.student
    
    # Блокируем аккаунт студента (предполагаем, что у студента есть поле is_active)
    if hasattr(student, 'is_active'):
        student.is_active = False
        student.save()
        messages.success(request, f'Аккаунт студента {student.full_name} заблокирован')
    else:
        messages.error(request, 'У студента нет поля is_active для блокировки')
    
    return redirect('debts:list')


@login_required
@admin_required
def pay_debt(request, debt_id):
    """Погасить долг студента"""
    debt = get_object_or_404(Debt, pk=debt_id)
    
    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        
        if payment_method_id:
            payment_method = get_object_or_404(PaymentMethod, pk=payment_method_id)
            
            # Создаем оплату за текущий месяц
            payment = Payment.objects.create(
                student=debt.student,
                course=debt.course,
                amount=debt.total_amount,
                payment_method=payment_method,
                paid_at=timezone.now().date(),
                months_paid=[debt.month],
                month_count=1,
                comment=f'Погашение долга за {debt.month}.{debt.year}',
                created_by=request.user
            )
            
            # Обновляем статус долга
            debt.status = 'paid'
            debt.paid_amount = debt.total_amount
            debt.save()
            
            messages.success(request, f'Долг студента {debt.student.full_name} погашен')
            
            # Если у студента были другие долги, разблокируем аккаунт
            other_debts = Debt.objects.filter(
                student=debt.student, 
                status='active'
            ).exclude(pk=debt.pk).exists()
            
            if not other_debts and hasattr(debt.student, 'is_active'):
                debt.student.is_active = True
                debt.student.save()
                messages.info(request, f'Аккаунт студента {debt.student.full_name} разблокирован')
        else:
            messages.error(request, 'Выберите способ оплаты')
    
    return redirect('debts:list')


@require_POST
@login_required
@admin_required
def update_debtors_api(request):
    """API endpoint для обновления списка должников"""
    try:
        from django.core.management import call_command
        
        # Вызываем management command
        call_command('update_debtors')
        
        return JsonResponse({'success': True, 'message': 'Должники успешно обновлены'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
