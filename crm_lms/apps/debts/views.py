from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from django.http import HttpResponse

from apps.core.mixins import admin_required
from .models import Debt


@login_required
@admin_required
def debt_list(request):
    qs = Debt.objects.select_related('student', 'course').filter(status='active')
    course_id = request.GET.get('course')
    if course_id:
        qs = qs.filter(course_id=course_id)

    total_debt = qs.aggregate(s=Sum('total_amount'))['s'] or 0
    total_paid = qs.aggregate(s=Sum('paid_amount'))['s'] or 0

    context = {
        'debts': qs,
        'total_debt': total_debt,
        'total_paid': total_paid,
        'total_remaining': total_debt - total_paid,
        'page_title': 'Должники',
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
