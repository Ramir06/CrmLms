from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Q

from apps.core.mixins import admin_required
from .models import Payment
from apps.students.models import Student
from apps.courses.models import Course


from django import forms


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'course', 'amount', 'payment_method', 'paid_at', 'comment']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'paid_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


@login_required
@admin_required
def payment_list(request):
    qs = Payment.objects.select_related('student', 'course', 'created_by').all()

    course_id = request.GET.get('course')
    method = request.GET.get('method')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('q', '')

    if course_id:
        qs = qs.filter(course_id=course_id)
    if method:
        qs = qs.filter(payment_method=method)
    if date_from:
        qs = qs.filter(paid_at__gte=date_from)
    if date_to:
        qs = qs.filter(paid_at__lte=date_to)
    if search:
        qs = qs.filter(Q(student__full_name__icontains=search))

    total = qs.aggregate(s=Sum('amount'))['s'] or 0
    courses = Course.objects.filter(is_archived=False)

    context = {
        'payments': qs[:200],
        'total': total,
        'courses': courses,
        'page_title': 'Оплаты',
        'filter_course': course_id,
        'filter_method': method,
    }
    return render(request, 'admin/payments/list.html', context)


@login_required
@admin_required
def payment_create(request):
    form = PaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.created_by = request.user
        payment.save()
        messages.success(request, 'Оплата добавлена.')
        return redirect('payments:list')
    return render(request, 'admin/payments/form.html', {'form': form, 'page_title': 'Добавить оплату'})


@login_required
@admin_required
def payment_delete(request, pk):
    obj = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Оплата удалена.')
    return redirect('payments:list')


@login_required
@admin_required
def payment_export(request):
    import openpyxl
    from django.utils import timezone
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Оплаты'
    ws.append(['ID', 'Студент', 'Курс', 'Сумма', 'Способ', 'Дата'])
    for p in Payment.objects.select_related('student', 'course').all():
        ws.append([p.pk, p.student.full_name, p.course.title, float(p.amount),
                   p.get_payment_method_display(), str(p.paid_at)])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=payments_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response
